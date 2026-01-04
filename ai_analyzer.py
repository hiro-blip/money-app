import google.generativeai as genai
import json

def analyze_receipt(api_key, image_data, categories):
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-flash-latest')
    
    category_str = "・".join(categories)
    prompt = f"画像を読み取り、JSON形式で出力してください。項目: date(YYYY/MM/DD), store, item, price(数値), category({category_str}から選択)"
    
    image_parts = [{"mime_type": "image/jpeg", "data": image_data}]
    response = model.generate_content([prompt, image_parts[0]])
    
    # 余計な装飾を消してJSONとして読み込む
    clean_json = response.text.replace("```json", "").replace("```", "").strip()
    return json.loads(clean_json)
def get_ai_advice(api_key, total_assets, spent, budget, categories_summary):
    genai.configure(api_key=api_key)
    # 👇 レシート解析と同じ 'gemini-flash-latest' に変更します
    model = genai.GenerativeModel('gemini-flash-latest')
    
    prompt = f"""
    あなたは優秀な家計再生コンサルタントです。以下の家計データを見て、
    ユーザーが節約したくなるような前向きで具体的なアドバイスを100文字程度で作成してください。
    
    ・総資産: {total_assets}円
    ・今月の支出: {spent}円
    ・月間予算: {budget}円
    ・支出の内訳: {categories_summary}
    """
    
    response = model.generate_content(prompt)
    return response.text