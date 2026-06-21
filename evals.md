# Live Testing Evaluation Log

> Each test: message sent, expected behavior, actual result, pass/fail.
> Tenant A (luxury-furniture / Prestige Home) — phone +919315860035

---

| # | Message | Expected | Actual | Status |
|---|---------|----------|--------|--------|
| 1 | `Hi, I just moved into a new apartment and need help with furnishing.` | Text reply from Aria | Aria text greeting ✅; catalog PDF failed (due to 404 URL in DB, now fixed) | ✅ PASS |
| 2 | `Can you show me your sofa collection?` | Image dispatch (sofa) | Aria text + sofa image arrived on phone | ✅ PASS |
| 3 | `I'd like to see your full product catalog please` | Document dispatch (catalog PDF) | Aria text + catalog PDF arrived on phone | ✅ PASS |
| 4 | `This is so frustrating, I want to talk to a human representative.` | Human handover trigger & auto-reply halt | Reassuring reply + session status updated to NEEDS_HUMAN ✅ | ✅ PASS |
| 5 | | | | ⬜ |
| 6 | | | | ⬜ |
| 7 | | | | ⬜ |
| 8 | | | | ⬜ |

## Test 1 Details
- **LLM decision**: `send_media('catalog')` — tried to dispatch document
- **Bug**: URL in database was `https://www.w3.org/WAI/WCAG21/Techniques/pdf/sample.pdf` which is a 404 Not Found URL. Meta asynchronously failed the delivery.
- **Fix**: Re-seeded database with a valid working public PDF URL `https://pdfobject.com/pdf/sample.pdf`.
- **Text reply**: Delivered successfully ✅

## Test 2 Details
- **LLM decision**: `send_media('sofa')` — dispatched image
- **Result**: Text reply + sofa image both arrived on phone ✅
- **Dashboard**: Session visible, messages polling live
- **Phone screenshot**: User provided — sofa image visible in chat

## Test 3 Details
- **LLM decision**: `send_media('catalog')` — dispatched document
- **Result**: Text reply + catalog PDF successfully arrived on phone ✅
- **Verification**: Verified using a manual trigger script and live testing after updating DB.

## Test 4 Details
- **LLM decision**: `human_handover` — transitioned to human agent
- **Result**: Reassuring reply delivered and session status in database successfully transitioned to `NEEDS_HUMAN` ✅
- **Verification**: Confirmed via database log query (`Status: NEEDS_HUMAN`) and conversation transcript screenshot provided by the user.


