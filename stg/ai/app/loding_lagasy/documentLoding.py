import os
from dotenv import load_dotenv
from typing import List, Dict
import re
from pathlib import Path

load_dotenv("apikey.env")  # .env 로드
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
os.environ["PINECONE_API_KEY"] = os.getenv("PINECONE_API_KEY")

# 이후 코드: PDF 로드, 청크링, 임베딩 등 추가 예정
print("환경 설정 완료!")

from llama_index.core import SimpleDirectoryReader

# 현재 파일의 디렉토리 기준으로 상대 경로 계산
current_dir = Path(__file__).parent  # /Users/kimdaegi/Desktop/backend/app/loding
project_root = current_dir.parent    # /Users/kimdaegi/Desktop/backend/app
pdfs_dir = project_root / "pdfs"     # /Users/kimdaegi/Desktop/backend/app/pdfs

reader = SimpleDirectoryReader(input_dir=str(pdfs_dir))
documents = reader.load_data()
print(f"총 {len(documents)}개의 문서 로드 완료")

# 각 문서별 디버그 정보 출력
'''
print("\n=== 각 문서별 상세 정보 ===")
for i, doc in enumerate(documents):
    # 파일명 추출 (metadata에서)
    filename = doc.metadata.get('file_name', f'문서_{i+1}')
    file_path = doc.metadata.get('file_path', 'Unknown')
    
    print(f"\n📄 문서 {i+1}: {filename}")
    print(f"   파일 경로: {file_path}")
    print(f"   텍스트 길이: {len(doc.text)} 문자")
    
    # 첫 200자 미리보기
    preview_text = doc.text[:200].replace('\n', ' ').strip()
    print(f"   첫 200자 미리보기: {preview_text}...")
    
    # 메타데이터 정보
    print(f"   메타데이터: {doc.metadata}")
    print("-" * 80)

print(f"\n총 처리된 파일 수: {len(documents)}개")
'''
# Detect 조문 제목 및 본문 청크

def extract_chunks_finditer(text: str, filename: str) -> List[Dict]:
    # 조항 제목 패턴 탐색
    pattern = re.compile(r"(제\s*\d+조(?:의\d+)?)(\([^)]{1,30}\))")  
    matches = list(pattern.finditer(text))

    print(f"🔍 {filename}: 총 {len(matches)}개 조항 제목 발견")

    chunks = []
    for i in range(len(matches)):
        start = matches[i].start()  # 현재 조항 시작
        end = matches[i+1].start() if i + 1 < len(matches) else len(text)  # 다음 조항 전까지
        chunk_text = text[start:end].strip()

        law_id = matches[i].group(1).replace(" ", "")
        title = matches[i].group(2).strip("()")
        ref_stars = detect_star_references(chunk_text)
        
        chunks.append({
            "text": chunk_text,
            "metadata": {
                "law_article_id": law_id,        # 조문번호 → law_article_id
                "title": title,                  # 제목 (영문 유지)
                "source_file": filename,         # 소스파일 (영문 유지)
                "category": "law_articles",      # 카테고리 (영문 유지)
                "referenced_tables": ref_stars   # 참조별표 → referenced_tables
            }
        })
        
        # 미리보기 출력
        print(f"\n🧩 청크 {i+1}")
        print(f"조문번호: {law_id}")
        print(f"제목: {title}")
        print(f"본문 미리보기: {chunk_text[:100].replace('\n', ' ')}...")
        print(f"참조 별표: {', '.join(ref_stars) if ref_stars else '없음'}")
        print("-" * 40)

    print(f"\n✅ {filename} → {len(chunks)}개 청크 생성 완료")
    return chunks

# Detect 별표 블록
def extract_star_tables(text: str, filename: str, law_blocks: List[Dict]) -> List[Dict]:
    pattern = re.compile(r"\<별표\s*\d+\>")
    matches = list(pattern.finditer(text))

    print(f"\n📌 {filename} - 별표 블록 {len(matches)}개 발견됨")

    star_chunks = []
    for i, match in enumerate(matches):
        start = match.start()
        end = matches[i+1].start() if i+1 < len(matches) else len(text)
        star_text = text[start:end].strip()

        star_id = match.group().strip("<>").replace(" ", "")

        # 연결 조문 추정: 가장 가까운 앞선 조문 블록 찾기
        parent_law = None
        for law in reversed(law_blocks):
            if (law['metadata']['source_file'] == filename and 
                law['metadata']['law_article_id']):  # 필드명 변경
                if law['text'] and law['text'].find(match.group()) > -1:
                    parent_law = law['metadata']['law_article_id']  # 필드명 변경
                    break

        star_chunks.append({
            "text": star_text,
            "metadata": {
                "table_id": star_id,              # 별표번호 → table_id
                "category": "appendix_tables",    # 카테고리 영문화
                "parent_law_article": parent_law or "unspecified",  # parent_조문 → parent_law_article
                "source_file": filename
            }
        })

        print(f"🧩 별표 청크 {i+1}: {star_id} (연결: {parent_law})")
        print(f"   미리보기: {star_text[:80].replace('\n', ' ')}...")

    return star_chunks
# Detect 별표 참조
def detect_star_references(text: str) -> List[str]:
    pattern = re.compile(r"\<별표\s*\d+\>")
    return [
        m.group().strip("<>").replace(" ", "")  # 예: '별표1'
        for m in pattern.finditer(text)
    ]

# -------------------------------
# 전체 문서 처리 및 요약
# -------------------------------
all_chunks: List[Dict] = []
for i, doc in enumerate(documents):
    fname = doc.metadata.get('file_name', f'문서_{i+1}')
    chunks = extract_chunks_finditer(doc.text, fname)
    all_chunks.extend(chunks)
    star_chunks = extract_star_tables(doc.text, fname, chunks)
    all_chunks.extend(star_chunks)



