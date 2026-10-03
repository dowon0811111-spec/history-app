import os
from dotenv import load_dotenv
from anthropic import Anthropic
import streamlit as st
from datetime import datetime
import requests
import json
import re

load_dotenv()

client = Anthropic(
    base_url=os.getenv("ANTHROPIC_BASE_URL"),
    api_key=os.getenv("ANTHROPIC_API_KEY"),
)

def ask_ai(prompt):
    res = client.messages.create(
        model="claude-haiku",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}]
    )
    return res.content[0].text

def get_person_image(person_name):
    """위키피디아에서 위인의 사진을 가져온다"""
    try:
        # 위키피디아 API로 해당 인물 검색
        url = "https://en.wikipedia.org/w/api.php"
        params = {
            "action": "query",
            "titles": person_name,
            "prop": "pageimages",
            "pithumbsize": 300,
            "format": "json"
        }
        response = requests.get(url, params=params, timeout=5)
        data = response.json()

        pages = data.get("query", {}).get("pages", {})
        for page in pages.values():
            if "thumbnail" in page:
                return page["thumbnail"]["source"]

        return None
    except Exception as e:
        print(f"이미지 검색 실패: {e}")
        return None

def save_history(user_name, result_text):
    """분석 결과를 history.json에 저장한다"""
    try:
        # 현재 날짜 및 시간
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 결과에서 위인 정보 파싱
        records = []
        sections = re.split(r'\*\*위인 \d+:', result_text)

        for i, section in enumerate(sections[1:], 1):
            # 위인 이름과 영어 이름 추출
            name_match = re.search(r'^([^(]+)\s*\(([^)]+)\)', section)
            if name_match:
                person_name = name_match.group(1).strip()
                english_name = name_match.group(2).strip()

                # 업적과 유사점 추출
                achievement_match = re.search(r'주요 업적:\s*([^\n-]+)', section)
                achievement = achievement_match.group(1).strip() if achievement_match else ""

                similarity_matches = re.findall(r'나와의 유사점:\s*((?:[^\n]+\n?)+)', section)
                similarities = []
                if similarity_matches:
                    similarity_text = similarity_matches[0]
                    similarities = [s.strip() for s in similarity_text.split('\n') if s.strip() and not s.strip().startswith('- ')]
                    if not similarities:
                        # "-" 형식으로 된 리스트 파싱
                        similarities = [s.strip()[2:] if s.strip().startswith('- ') else s.strip()
                                       for s in similarity_text.split('\n') if s.strip()]

                # 사진 URL 가져오기
                image_url = get_person_image(english_name)

                record = {
                    "rank": i,
                    "name": person_name,
                    "english_name": english_name,
                    "image_url": image_url,
                    "achievement": achievement,
                    "similarities": similarities[:3]  # 최대 3개까지만
                }
                records.append(record)

        # JSON 구조
        history_data = {
            "title": f"{user_name}의 위인 분석 결과 - {now}",
            "user_name": user_name,
            "timestamp": now,
            "records": records
        }

        # 기존 파일이 있으면 로드해서 추가
        if os.path.exists("history.json"):
            with open("history.json", "r", encoding="utf-8") as f:
                existing_data = json.load(f)
                if isinstance(existing_data, list):
                    existing_data.append(history_data)
                    all_data = existing_data
                else:
                    all_data = [existing_data, history_data]
        else:
            all_data = [history_data]

        # 파일 저장
        with open("history.json", "w", encoding="utf-8") as f:
            json.dump(all_data, f, ensure_ascii=False, indent=2)

        return True
    except Exception as e:
        print(f"히스토리 저장 실패: {e}")
        return False

def load_history():
    """history.json에서 모든 기록을 로드한다"""
    try:
        if os.path.exists("history.json"):
            with open("history.json", "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
                else:
                    return [data]
        return []
    except Exception as e:
        print(f"히스토리 로드 실패: {e}")
        return []