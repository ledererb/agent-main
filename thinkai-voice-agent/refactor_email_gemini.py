import re
import sys

def main():
    try:
        with open('email_processor.py', 'r', encoding='utf-8') as f:
            content = f.read()

        # Remove anthropic import, add genai
        content = content.replace("from anthropic import AsyncAnthropic", "from google import genai\nfrom google.genai import types")

        # Replace anthropic key check
        old_key_check = """    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    if not anthropic_key:
        logger.error("Nincs ANTHROPIC_API_KEY beállítva. E-mail feldolgozás megszakítva.")
        return"""
        
        new_key_check = """    google_key = os.getenv("GOOGLE_API_KEY")
    if not google_key:
        logger.error("Nincs GOOGLE_API_KEY beállítva. E-mail feldolgozás megszakítva.")
        return"""
        
        content = content.replace(old_key_check, new_key_check)

        # Replace API call
        old_api_call = """    client = AsyncAnthropic(api_key=anthropic_key)
    
    user_content = f"--- BEJÖVŐ E-MAIL ---\\nFeladó: {from_name} <{from_email}>\\nTárgy: {subject}\\nÜzenet:\\n{text_content}\\n"
    
    if knowledge:
        sys_prompt += f"\\n\\n--- TUDÁSBÁZIS ---\\n{knowledge}"
    sys_prompt += f"\\n\\n--- JSON UTASÍTÁS ---\\n{json_instruction}"

    logger.info(f"Claude 3.5 Sonnet elemzi az e-mailt: {from_email} - {subject}")
    try:
        response = await client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=2048,
            system=sys_prompt,
            messages=[{"role": "user", "content": user_content}],
            temperature=0.2
        )
        ai_text = response.content[0].text.strip()
    except Exception as e:
        logger.error(f"Anthropic API hiba: {e}")
        # Mivel a levél már Seen állapotba került, de hiba volt,
        # éles rendszerben vissza lehetne állítani Unseen-re.
        return"""

        new_api_call = """    client = genai.Client(api_key=google_key)
    
    user_content = f"--- BEJÖVŐ E-MAIL ---\\nFeladó: {from_name} <{from_email}>\\nTárgy: {subject}\\nÜzenet:\\n{text_content}\\n"
    
    if knowledge:
        sys_prompt += f"\\n\\n--- TUDÁSBÁZIS ---\\n{knowledge}"
    sys_prompt += f"\\n\\n--- JSON UTASÍTÁS ---\\n{json_instruction}"

    logger.info(f"Gemini 2.5 Flash elemzi az e-mailt: {from_email} - {subject}")
    try:
        response = await client.aio.models.generate_content(
            model="gemini-2.5-flash",
            contents=user_content,
            config=types.GenerateContentConfig(
                system_instruction=sys_prompt,
                temperature=0.2,
                response_mime_type="application/json"
            )
        )
        ai_text = response.text.strip()
    except Exception as e:
        logger.error(f"Gemini API hiba: {e}")
        # Mivel a levél már Seen állapotba került, de hiba volt,
        # éles rendszerben vissza lehetne állítani Unseen-re.
        return"""

        content = content.replace(old_api_call, new_api_call)

        with open('email_processor.py', 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("Successfully migrated email_processor.py to Gemini 2.5 Flash")

    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    main()
