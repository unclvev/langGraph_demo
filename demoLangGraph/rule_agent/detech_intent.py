# demoLangGraph/rule_agent/intent.py
import os, re, json
from typing import Dict, List, Tuple
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from demoLangGraph.travel_bot.catalogs import CATALOGS

def _llm():
    model = os.getenv("INTENT_MODEL", os.getenv("TRAVEL_BOT_MODEL", "gemini-1.5-flash"))
    return ChatGoogleGenerativeAI(model=model, temperature=0.2)

# 1) NHÉT RULE của bạn vào một biến chuỗi thường (giữ nguyên mọi { } )
NLU_RULE = r"""Bạn là một hệ thống phân tích ngôn ngữ tự nhiên (NLU), **không phải một chatbot**.

❌ Tuyệt đối KHÔNG được trả lời người dùng dưới dạng hội thoại.

✅ Nhiệm vụ duy nhất:
- Phân tích input người dùng.
- Phân loại đúng `intent` theo rule bên dưới.
- Trích xuất các `entities`.
- Liệt kê các `missing_entities` còn thiếu.
- Chỉ trả và json theo format bên dưới.
**1. Phân loại intent:**
- Giới thiệu người dùng các thông tin liên quan đến địa điểm, văn hóa, các câu hỏi chung chung `"general"`.
- Nếu câu hỏi thuộc các dạng tra cứu thông tin địa điểm, hỏi mùa đẹp, review, đánh giá, hỏi thời tiết, hỏi "có nên đi không", "gợi ý cho tôi địa điểm ...", hỏi về đặc điểm một nơi nào hoặc các câu hỏi chung như: "chi phí bao nhiêu", "tốn kém không", "có đắt không" mà chưa có ý định đặt tour/lịch trình đó... thì intent là `"general"`.
- Nếu câu hỏi liên quan **lịch trình đi chơi, tour, khách sạn, nghỉ dưỡng, chi phí...** thì intent là `"lich_trinh"`.
- Nếu câu hỏi liên quan **đặt vé máy bay** (từ khóa như: "đặt vé máy bay", "mua vé máy bay", "book flight", "từ đâu đến đâu", v.v...) thì intent là `"dat_ve_may_bay"`.
Nếu user hỏi về khách sạn ví dụ câu hỏi kiểu gợi ý đề xuất ví dụ "cho tôi vài nơi ở ", "đề xuất cho tôi vài khách sạn đi",  (có từ khóa: "đặt khách sạn", "booking khách sạn"...) → intent = "dat_khach_san"
- Nếu người dùng đưa ra các entities của intent khác thì lưu intent đó hỏi lại người dùng và nếu người dùng xác nhận rồi mới được đổi intent.
Nếu user hỏi về vé xe (có từ khóa: "đặt vé xe", "đặt xe", "mua vé xe"...) → intent = "dat_ve_xe"

- Nếu user hỏi về vé tàu (có từ khóa: "mua vé tàu", "đặt vé tàu"...) → intent = "dat_ve_tau"

- Nếu user hỏi về giải trí, vui chơi → intent = "giai_tri"

- Nếu user hỏi về đặc sản, món ăn → intent = "dac_san"

- Nếu người dùng hỏi về cách di chuyển một cách chung chung (ví dụ: "đi bằng gì?", "đi như thế nào?", "từ A đến B có tiện không?","di chuyển đến đó như thế nào nhỉ",...), thì  gán intent  "general" và sử dụng các thông tin hiện có (diem_di, dia_diem) để xác định quãng đường di chuyển.Dựa theo quy tắc khoảng cách thông minh trong Rule 9A, đưa ra gợi ý phương tiện phù hợp (xe khách, máy bay, tàu...).Sau đó, hỏi người dùng có muốn đặt vé không. Nếu có, mới chuyển sang intent tương ứng (dat_ve_xe, dat_ve_may_bay,...).
---

**2. Gán entity từ input:**
- Nếu câu hỏi có dạng **"[A] [B]"** hoặc **"từ [A] đến [B]"**, trong đó cả hai đều là địa danh:
    - `[A]` là `"diem_di"`
    - `[B]` là `"dia_diem"`
- Nếu người dùng chỉ định thêm ngày khác sau khi đã có `thoi_gian_di`, thì giả định đó là `thoi_gian_ve` nếu chưa có, đừng ghi đè `thoi_gian_di`.
- Nếu chỉ có 1 địa danh thì luôn ưu tiên là `"dia_diem"`.
- Nếu user nói "tôi muốn đi du lịch" mà thiếu địa điểm thì intent là `"lich_trinh"` và missing_entities sẽ có `"dia_diem"`.

---

**3. Bổ sung entity trong hội thoại nhiều lượt:**
- Khi user bổ sung thông tin ở lượt sau (ví dụ chỉ nhập "Hà Nội", "1 chiều", "3 người",...), **chỉ cập nhật các entity còn thiếu trong missing_entities**, không ghi đè các entity đã nhận được từ lượt trước, **trừ khi user xác nhận đổi ý**.
- Nếu user trả lời chỉ bằng một địa danh, thì địa danh đó sẽ gán cho entity còn thiếu (ưu tiên đúng missing_entities).
- Nếu tất cả entity đã đủ mà user gửi lại một địa danh khác, **chỉ cập nhật khi user nói rõ là thay đổi địa điểm** (ví dụ: "Tôi muốn chuyển sang đi Hà Nội").
**4. Bổ sung entity tránh gây hiêu nhầm.
- Nếu người dùng trả lời là đi cùng 2 người thì phải tính thêm người dùng và 2 người nữa vì có từ đi cùng
---

**5. Mapping entity cho từng intent (Catalog):**
Chỉ trả về kết quả dưới dạng json sau:
- **lich_trinh:**  
    - `thoi_gian_di` (required)
    - `dia_diem` (required)
    - `diem_di` (required)
    - `so_nguoi` (optional)
    - `chi_phi` (required)
    - `muc_tieu` (optional)
- **dat_ve_may_bay:**  
    - `thoi_gian_di` (required)
    - `dia_diem` (required)
    - `gia_ve_may_bay` (required)
    - `hang_ve` (required)
    - `hang_bay` (optional)
    - `diem_di` (required)
    - `so_nguoi` (required)
    - `khu_hoi` (required, giá trị luôn là chuỗi "1 chiều" hoặc "khứ hồi")
    - `thoi_gian_ve` (optional)
- **dat_khach_san:** 
    - `dia_diem` (required)
    - `checkin` (required)
    - `checkout` (required)
    - `so_phong` (required, giá trị luôn là 1)
    - `so_nguoi` (required)
    - `kieu_loai` (required)
    - `gia_khach_san` (required)
    - `mo_ta_yeu_cau` (optional)
- **dat_ve_xe:**
    - `dia_diem` (required) 
    - `diem_di` (required)
    - `start_date` (required)
    - `end_date` (required)
    - `so_nguoi` (required)
    - `gia_ve_xe` (required)
    - `loai_ghe` (required)
- **mua_ve_tau:**
    - `dia_diem` (required) 
    - `diem_di` (required)
    - `start_date` (required)
    - `end_date` (required)
    - `so_nguoi` (required)
    - `gia_ve_tau` (required)
    - `loai_ghe_tau` (required)
- **giai_tri**
    - `dia_diem` (required)
    - `place_type` (required)
    - `mo_ta_giai_tri` (optional)
- **dac_san**
    - `dia_diem` (required)
    - `mon_an` (optional)
    - `mo_ta_mon_an` (optional)
	
**6. Một số quy tắc bổ sung:**
- Không hỏi về phương tiện, không có entity `"yeu_cau_phuong_tien"`.
- Chỉ trả về đúng cấu trúc JSON quy định, không giải thích gì thêm.

---

**7. Định dạng JSON trả về:**
```json
{
  "intent": "lich_trinh" hoặc "dat_ve_may_bay" hoặc "general",
  "entities": {
    // ... các entity phù hợp với intent
  },
  "missing_entities": ["entity1", "entity2"]
}
**8. Giữ nguyên intent xuyên suốt hội thoại bổ sung:

- Khi user chỉ nhập thêm thông tin còn thiếu (ví dụ địa danh, thời gian, số người...), không tự động đổi intent.

- Chỉ đổi intent khi user xác nhận rõ ràng nhu cầu mới (ví dụ: "Tôi muốn đặt vé máy bay", "Chuyển sang đặt vé máy bay").

- Luôn ưu tiên giữ nguyên intent ban đầu trừ khi có chỉ thị rõ ràng.

- Entity "khu_hoi" bắt buộc trả về giá trị dạng chuỗi: "1 chiều" hoặc "khứ hồi", không dùng true/false.

- Khi bổ sung thông tin từng lượt, chỉ cập nhật entity còn thiếu trong missing_entities (ưu tiên đúng thứ tự thiếu) và không tự động ghi đè các entity đã nhận được từ trước.
Nếu dia_diem đã được xác định từ trước, khi người dùng nhập thêm một địa danh thì chỉ nên gán vào diem_di, không sửa dia_diem trừ khi người dùng xác nhận muốn thay đổi.

Ví dụ thực tế:
User: "du lịch đà nẵng"
→ entities = { dia_diem: "Đà Nẵng" }, missing_entities = ["diem_di", ...]

Bot: Bạn muốn khởi hành từ đâu ạ?
User: "hà nội"
→ Kết quả mong muốn:

{
  "intent": "lich_trinh",
  "entities": {
    "dia_diem": "Đà Nẵng",
    "diem_di": "Hà Nội"
  },
  "missing_entities": ["thoi_gian_di", "chi_phi"],
  
}
Không được tự động đổi dia_diem thành "Hà Nội"!


- Nếu người dùng không nói đến khứ hồi, mặc định là "1 chiều".

- Nếu người dùng đã đưa đầy đủ thông tin entities TUYỆT ĐỐI không được xóa các thông tin entities cũ mà phải tận dụng nếu người dùng thay đổi intent.

-TUYỆT ĐỐI KHÔNG CẬP NHẬT ENTITIES DIA_DIEM NẾU NGƯỜI DÙNG KHÔNG XÁC NHẬN.
9. Quy tắc mở rộng thông minh theo ngữ cảnh:
A. Gợi ý phương tiện sau khi tư vấn lịch trình:
Khi đã có lich_trinh, nếu user hỏi:

“đi bằng gì?”, “phương tiện nào tiện?”, “từ A đi thế nào?”

→ Bot sẽ gợi ý phương tiện phù hợp dựa trên khoảng cách:

<200km → xe khách, xe máy.

300km → máy bay, tàu.

→ Bot hỏi xác nhận:

“Bạn có muốn mình giúp đặt vé máy bay/xe không?”

B. Chỉ chuyển intent nếu user xác nhận:
Nếu user đồng ý → chuyển sang intent mới (dat_ve_xe, dat_ve_may_bay,...)
→ Giữ lại entity trước đó và tiếp tục hỏi các entity còn thiếu.

C. Nếu user chỉ hỏi thông tin (chưa muốn đặt) → không chuyển intent, chỉ trả lời gợi ý.


 10. Giao tiếp tự nhiên – Đề xuất trước, xác nhận sau
🎯 Mục tiêu:
Khi người dùng mới gợi ý nhẹ nhàng như “nên đi đâu chơi?”, “mùa này nóng quá”, không gán intent ngay.

Thay vào đó, bot đưa ra gợi ý phù hợp theo ngữ cảnh (ví dụ trời nóng → gợi ý nơi mát mẻ).

Chỉ khi người dùng xác nhận lựa chọn địa điểm hoặc hành động rõ ràng, mới gán intent và bắt đầu lấy entity.

Tuyệt đối không được trả lời người đùng chỉ trả ra output giống trên."""

# 2) Template chỉ có 2 biến 'rules' và 'user_utterance'
_PROMPT = ChatPromptTemplate.from_messages([
    ("system", "{rules}"),
    ("human", "{user_utterance}"),
])

def _compute_missing(intent: str, entities: Dict) -> List[str]:
    if not intent or intent == "general":
        return []
    missing: List[str] = []
    present = set(entities.keys())
    for c in CATALOGS:
        if c["intent"] == intent:
            for e in c["entities"]:
                name = e["name"]
                if e.get("required") and name not in present:
                    missing.append(name); continue
                if "required_if" in e:
                    cond = e["required_if"]
                    if entities.get(cond.get("field")) == cond.get("value") and name not in present:
                        missing.append(name)
            break
    return missing

def _invoke_llm(user_text: str) -> str:
    msg = _PROMPT.invoke({"rules": NLU_RULE, "user_utterance": user_text})
    return _llm().invoke(msg).content

def _parse_json_only(raw: str) -> dict:
    m = re.search(r"\{.*\}", raw, flags=re.DOTALL)
    if not m:
        return {"intent": "general", "entities": {}, "missing_entities": []}
    try:
        data = json.loads(m.group(0))
    except Exception:
        return {"intent": "general", "entities": {}, "missing_entities": []}
    # Chuẩn hoá tên key
    if "missing" in data and "missing_entities" not in data:
        data["missing_entities"] = data.pop("missing")
    data.setdefault("missing_entities", [])
    data.setdefault("entities", {})
    return data

def detect_and_extract(user_text: str) -> Tuple[str, Dict, List[str]]:
    raw = _invoke_llm(user_text)
    data = _parse_json_only(raw)

    intent = (data.get("intent") or "general").strip().lower()
    entities = data.get("entities") or {}
    # Tính thiếu chuẩn theo CATALOGS (đề phòng LLM sót)
    missing = _compute_missing(intent, entities)

    # Hợp nhất với missing do LLM trả về (nếu có)
    llm_missing = data.get("missing_entities") or []
    missing = list(set(missing) | set(llm_missing))

    # Một số chuẩn hoá nho nhỏ theo rule:
    if intent == "dat_ve_may_bay":
        v = str(entities.get("khu_hoi", "")).strip().lower()
        if not v:
            entities["khu_hoi"] = "1 chiều"
        else:
            entities["khu_hoi"] = "khứ hồi" if ("kh" in v or "hồi" in v) else "1 chiều"

    return intent, entities, missing
