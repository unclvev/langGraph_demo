import redis
import json
import time
import warnings
from typing import List, Dict, Optional

warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=FutureWarning)


class ShortTermMemory:
    """Quản lý bộ nhớ ngắn hạn cho chatbot sử dụng Redis"""

    def __init__(self, user_id: str, redis_host: str = "localhost", redis_port: int = 6379, redis_db: int = 0):
        self.user_id = user_id
        self.redis_client = redis.Redis(
            host=redis_host,
            port=redis_port,
            db=redis_db,
            decode_responses=True  # Tự động decode UTF-8
        )
        self._test_connection()

    def _test_connection(self):
        """Test kết nối Redis"""
        try:
            self.redis_client.ping()
            print("Redis kết nối thành công")
        except Exception as e:
            print(f"Redis kết nối thất bại: {e}")
            raise ConnectionError(f"Không thể kết nối Redis: {e}")

    def add_turn(self, user_input: str, bot_response: str, ttl: int = 300):
        """
        Thêm một lượt hội thoại vào bộ nhớ ngắn hạn

        Args:
            user_input: Tin nhắn của user
            bot_response: Phản hồi của bot
            ttl: Thời gian sống (seconds), mặc định 5 phút
        """
        timestamp = int(time.time())
        key = f"stm:{self.user_id}:{timestamp}"

        data = {
            "user": user_input,
            "bot": bot_response,
            "timestamp": timestamp,
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp))
        }

        try:
            self.redis_client.set(key, json.dumps(data, ensure_ascii=False), ex=ttl)
            print(f"Đã lưu turn: {key} (TTL: {ttl}s)")
        except Exception as e:
            print(f"Lỗi khi lưu turn: {e}")

    def search(self, query: str, max_results: int = 10) -> List[Dict]:
        """
        Tìm kiếm các tin nhắn có chứa từ khóa

        Args:
            query: Từ khóa cần tìm
            max_results: Số kết quả tối đa

        Returns:
            List các tin nhắn chứa từ khóa, sắp xếp theo thời gian mới nhất
        """
        pattern = f"stm:{self.user_id}:*"
        keys = self.redis_client.keys(pattern)

        if not keys:
            return []

        # Sắp xếp theo timestamp (mới nhất trước)
        keys = sorted(keys, key=lambda x: int(x.split(':')[-1]), reverse=True)

        results = []
        query_lower = query.lower()

        for key in keys:
            if len(results) >= max_results:
                break

            try:
                msg_json = self.redis_client.get(key)
                if msg_json:
                    msg_data = json.loads(msg_json)
                    # Tìm trong cả user input và bot response
                    content = f"{msg_data.get('user', '')} {msg_data.get('bot', '')}".lower()
                    if query_lower in content:
                        results.append(msg_data)
            except json.JSONDecodeError:
                print(f"⚠️ Lỗi decode JSON cho key: {key}")
                continue

        print(f"Tìm thấy {len(results)} kết quả cho '{query}'")
        return results

    def get_recent(self, limit: int = 10) -> List[Dict]:
        """
        Lấy các tin nhắn gần đây nhất

        Args:
            limit: Số lượng tin nhắn tối đa

        Returns:
            List các tin nhắn gần đây, sắp xếp theo thời gian mới nhất
        """
        pattern = f"stm:{self.user_id}:*"
        keys = self.redis_client.keys(pattern)

        if not keys:
            return []

        # Sắp xếp theo timestamp (mới nhất trước)
        keys = sorted(keys, key=lambda x: int(x.split(':')[-1]), reverse=True)
        keys = keys[:limit]

        messages = []
        for key in keys:
            try:
                msg_json = self.redis_client.get(key)
                if msg_json:
                    messages.append(json.loads(msg_json))
            except json.JSONDecodeError:
                print(f"Lỗi decode JSON cho key: {key}")
                continue

        print(f"Lấy được {len(messages)} tin nhắn gần đây")
        return messages

    def get_conversation_context(self, limit: int = 5) -> str:
        """
        Lấy context cuộc hội thoại dưới dạng string để đưa vào prompt

        Args:
            limit: Số lượng turn gần đây nhất

        Returns:
            String chứa context cuộc hội thoại
        """
        recent_messages = self.get_recent(limit)

        if not recent_messages:
            return "Không có lịch sử hội thoại gần đây."

        context_lines = ["=== Lịch sử hội thoại gần đây ==="]

        # Đảo ngược để hiển thị theo thứ tự thời gian
        for msg in reversed(recent_messages):
            context_lines.append(f"User: {msg.get('user', '')}")
            context_lines.append(f"Bot: {msg.get('bot', '')}")
            context_lines.append("---")

        return "\n".join(context_lines)

    def clear(self):
        """Xóa tất cả bộ nhớ ngắn hạn của user"""
        pattern = f"stm:{self.user_id}:*"
        keys = self.redis_client.keys(pattern)

        if keys:
            deleted = self.redis_client.delete(*keys)
            print(f"Đã xóa {deleted} tin nhắn từ STM")
        else:
            print("Không có dữ liệu để xóa")

    def get_stats(self) -> Dict:
        """Lấy thống kê về bộ nhớ ngắn hạn"""
        pattern = f"stm:{self.user_id}:*"
        keys = self.redis_client.keys(pattern)

        if not keys:
            return {"total_messages": 0, "oldest": None, "newest": None}

        timestamps = [int(key.split(':')[-1]) for key in keys]
        timestamps.sort()

        return {
            "total_messages": len(keys),
            "oldest": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamps[0])),
            "newest": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamps[-1]))
        }

    def add_summary(self, summary: str, ttl: int = 600):
        """
        Lưu summary vào STM (dạng đặc biệt để sau này đẩy sang LTM)
        """
        timestamp = int(time.time())
        key = f"stm_summary:{self.user_id}:{timestamp}"

        data = {
            "summary": summary,
            "timestamp": timestamp,
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp))
        }

        try:
            self.redis_client.set(key, json.dumps(data, ensure_ascii=False), ex=ttl)
            print(f"Đã lưu summary vào STM: {key} (TTL: {ttl}s)")
        except Exception as e:
            print(f"Lỗi khi lưu summary: {e}")

    def extend_ttl(self, extend_seconds: int = 300):
        """
        Gia hạn TTL cho tất cả messages hiện có

        Args:
            extend_seconds: Số giây gia hạn thêm (mặc định 5 phút)
        """
        pattern = f"stm:{self.user_id}:*"
        keys = self.redis_client.keys(pattern)

        extended_count = 0
        for key in keys:
            current_ttl = self.redis_client.ttl(key)
            if current_ttl > 0:  # Chỉ gia hạn nếu chưa expire
                self.redis_client.expire(key, current_ttl + extend_seconds)
                extended_count += 1

        print(f"Đã gia hạn {extended_count} tin nhắn thêm {extend_seconds} giây")