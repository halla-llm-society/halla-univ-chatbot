import os
import sys
from loding.documentLoding import documents, extract_chunks_finditer, extract_star_tables
from loding.mongodbConnect import insert_chunks_to_mongo, collection
from typing import List, Dict
from loding.vector_db_upload import upload_chunks_to_pinecone, index, get_embedding
from loding.vector_db_upload import pc, index_name
from pinecone import Pinecone

# 올바른 인덱스 연결
index = pc.Index(index_name)  # "halla-academic-index" 사용

def test_full_pipeline():
    """PDF 로드 → 청크 생성 → MongoDB 저장 → Pinecone 업로드 전체 파이프라인 테스트"""
    
    print("=" * 60)
    print("           전체 파이프라인 테스트 시작")
    print("=" * 60)
    
    # 1. 문서 로드 확인
    print(f"📚 1단계: 문서 로드 완료 - {len(documents)}개 파일")
    
    # 2. 청크 생성
    print("\n📝 2단계: 청크 생성 중...")
    all_chunks: List[Dict] = []
    
    for i, doc in enumerate(documents):
        filename = doc.metadata.get('file_name', f'문서_{i+1}')
        print(f"\n처리 중: {filename}")
        
        # 조문 청크 생성
        law_chunks = extract_chunks_finditer(doc.text, filename)
        all_chunks.extend(law_chunks)
        
        # 별표 청크 생성
        star_chunks = extract_star_tables(doc.text, filename, law_chunks)
        all_chunks.extend(star_chunks)
        
        print(f"✅ {filename}: 조문 {len(law_chunks)}개 + 별표 {len(star_chunks)}개 = 총 {len(law_chunks) + len(star_chunks)}개 청크")
    
    print(f"\n📊 청크 생성 완료: 총 {len(all_chunks)}개")
    
    # 3. 청크 샘플 확인
    print("\n📖 3단계: 생성된 청크 샘플 (첫 번째 청크)")
    if all_chunks:
        sample_chunk = all_chunks[0]
        print("메타데이터:")
        for key, value in sample_chunk['metadata'].items():
            print(f"   {key}: {value}")
        print(f"\n내용 (길이: {len(sample_chunk['text'])} 문자):")
        print("-" * 40)
        print(sample_chunk['text'][:200] + "..." if len(sample_chunk['text']) > 200 else sample_chunk['text'])
        print("-" * 40)
    
    # 4. MongoDB 저장
    print("\n💾 4단계: MongoDB 저장 중...")
    insert_chunks_to_mongo(all_chunks)
    
    # 5. Pinecone 벡터 DB 업로드
    print("\n🚀 5단계: Pinecone 벡터 DB 업로드 중...")
    try:
        # 조문 카테고리 업로드 (영문 카테고리명 사용)
        upload_chunks_to_pinecone(category="law_articles")
        # 별표 카테고리 업로드 (영문 카테고리명 사용)
        upload_chunks_to_pinecone(category="appendix_tables")
        print("✅ Pinecone 업로드 완료!")
    except Exception as e:
        print(f"❌ Pinecone 업로드 실패: {e}")
    
    # 6. 저장 결과 확인
    print("\n🔍 6단계: 저장 결과 확인")
    total_docs = collection.count_documents({})
    print(f"MongoDB에 저장된 총 문서 수: {total_docs}개")
    
    # 파일별 저장 수 확인
    pipeline = [
        {"$group": {"_id": "$metadata.source_file", "count": {"$sum": 1}}},
        {"$sort": {"_id": 1}}
    ]
    file_counts = list(collection.aggregate(pipeline))
    print("\n파일별 저장된 청크 수:")
    for item in file_counts:
        print(f"   {item['_id']}: {item['count']}개")
    
    print("\n✅ 전체 파이프라인 테스트 완료!")
    return all_chunks

def test_mongodb_query():
    """MongoDB에서 데이터 조회 테스트"""
    
    print("\n" + "=" * 60)
    print("           MongoDB 조회 테스트")
    print("=" * 60)
    
    # 조문 타입 문서 조회
    law_docs = list(collection.find({"metadata.category": "law_articles"}).limit(2))
    print(f"📋 조문 타입 문서 수: {collection.count_documents({'metadata.category': 'law_articles'})}개")
    
    if law_docs:
        print(f"\n첫 번째 조문 샘플:")
        doc = law_docs[0]
        print(f"   조문번호: {doc['metadata'].get('law_article_id', 'N/A')}")
        print(f"   제목: {doc['metadata'].get('title', 'N/A')}")
        print(f"   파일: {doc['metadata'].get('source_file', 'N/A')}")
    
    # 별표 타입 문서 조회
    star_docs = list(collection.find({"metadata.category": "appendix_tables"}).limit(2))
    print(f"\n📌 별표 타입 문서 수: {collection.count_documents({'metadata.category': 'appendix_tables'})}개")
    
    if star_docs:
        print(f"\n첫 번째 별표 샘플:")
        doc = star_docs[0]
        print(f"   별표번호: {doc['metadata'].get('table_id', 'N/A')}")
        print(f"   연결 조문: {doc['metadata'].get('parent_law_article', 'N/A')}")
        print(f"   파일: {doc['metadata'].get('source_file', 'N/A')}")

def test_pinecone_vector_search():
    """Pinecone 벡터 검색 테스트"""
    
    print("\n" + "=" * 60)
    print("           Pinecone 벡터 검색 테스트")
    print("=" * 60)
    
    # 사용자가 직접 쿼리 입력할 수 있도록 개선
    print("검색 방법을 선택하세요:")
    print("1. 미리 정의된 쿼리로 테스트")
    print("2. 직접 쿼리 입력")
    
    search_choice = input("\n선택 (1-2): ")
    
    if search_choice == "1":
        # 미리 정의된 테스트 쿼리
        test_queries = [
            "학사 관리에 관한 규정",
            "별표에 관한 내용",
            "외국대학과의 학·석사 연계과정"
        ]
    elif search_choice == "2":
        # 사용자 입력 쿼리
        user_query = input("\n검색할 내용을 입력하세요: ").strip()
        if user_query:
            test_queries = [user_query]
        else:
            print("❌ 빈 쿼리입니다. 기본 쿼리를 사용합니다.")
            test_queries = ["학사 관리에 관한 규정"]
    else:
        print("❌ 잘못된 선택입니다. 기본 쿼리를 사용합니다.")
        test_queries = ["학사 관리에 관한 규정"]
    
    for query in test_queries:
        print(f"\n🔍 검색 쿼리: '{query}'")
        try:
            # 쿼리 임베딩 생성
            query_embedding = get_embedding(query)
            
            # 조문 카테고리에서 검색
            law_results = index.query(
                vector=query_embedding,
                top_k=3,
                namespace="law_articles",
                include_metadata=True
            )
            
            print(f"📋 조문 검색 결과 ({len(law_results.matches)}개):")
            for i, match in enumerate(law_results.matches):
                print(f"   {i+1}. 유사도: {match.score:.3f}")
                print(f"      조문: {match.metadata.get('law_article_id', 'N/A')}")
                print(f"      제목: {match.metadata.get('title', 'N/A')}")
                print(f"      미리보기: {match.metadata.get('text_preview', 'N/A')}")
            
            # 별표 카테고리에서 검색
            star_results = index.query(
                vector=query_embedding,
                top_k=2,
                namespace="appendix_tables",
                include_metadata=True
            )
            
            print(f"\n📌 별표 검색 결과 ({len(star_results.matches)}개):")
            for i, match in enumerate(star_results.matches):
                print(f"   {i+1}. 유사도: {match.score:.3f}")
                print(f"      별표: {match.metadata.get('table_id', 'N/A')}")
                print(f"      연결 조문: {match.metadata.get('parent_law_article', 'N/A')}")
                print(f"      미리보기: {match.metadata.get('text_preview', 'N/A')}")
            
        except Exception as e:
            print(f"❌ 검색 실패: {e}")
        
        print("-" * 50)

def test_pinecone_stats():
    """Pinecone 인덱스 통계 확인"""
    
    print("\n" + "=" * 60)
    print("           Pinecone 인덱스 통계")
    print("=" * 60)
    
    try:
        # 인덱스 통계
        stats = index.describe_index_stats()
        print(f"📊 총 벡터 수: {stats.total_vector_count}")
        print(f"📊 인덱스 크기: {stats.index_fullness:.2%}")
        
        if stats.namespaces:
            print("\n📋 네임스페이스별 벡터 수:")
            for namespace, info in stats.namespaces.items():
                print(f"   {namespace}: {info.vector_count}개")
        
    except Exception as e:
        print(f"❌ 통계 조회 실패: {e}")

def cleanup_test_data():
    """테스트 데이터 삭제"""
    
    print("\n" + "=" * 60)
    print("           테스트 데이터 삭제")
    print("=" * 60)
    
    # 삭제 전 데이터 수 확인
    before_count = collection.count_documents({})
    print(f"🗑️ 삭제 전 총 문서 수: {before_count}개")
    
    if before_count == 0:
        print("⚠️ 삭제할 데이터가 없습니다.")
        return
    
    # 사용자 확인
    response = input(f"\n정말로 모든 테스트 데이터({before_count}개)를 삭제하시겠습니까? (y/N): ")
    
    if response.lower() == 'y':
        # 모든 데이터 삭제
        result = collection.delete_many({})
        print(f"✅ 삭제 완료: {result.deleted_count}개 문서 삭제됨")
        
        # 삭제 후 확인
        after_count = collection.count_documents({})
        print(f"🔍 삭제 후 총 문서 수: {after_count}개")
    else:
        print("❌ 삭제 취소됨")

def cleanup_pinecone_data():
    """Pinecone 벡터 데이터 삭제"""
    
    print("\n" + "=" * 60)
    print("           Pinecone 데이터 삭제")
    print("=" * 60)
    
    try:
        # 현재 벡터 수 확인
        stats = index.describe_index_stats()
        total_vectors = stats.total_vector_count
        
        if total_vectors == 0:
            print("⚠️ 삭제할 벡터 데이터가 없습니다.")
            return
        
        print(f"🗑️ 삭제 대상 벡터 수: {total_vectors}개")
        
        # 사용자 확인
        response = input(f"\n정말로 모든 벡터 데이터({total_vectors}개)를 삭제하시겠습니까? (y/N): ")
        
        if response.lower() == 'y':
            # 모든 네임스페이스 삭제
            namespaces = list(stats.namespaces.keys()) if stats.namespaces else ["default"]
            
            for namespace in namespaces:
                index.delete(delete_all=True, namespace=namespace)
                print(f"✅ {namespace} 네임스페이스 삭제 완료")
            
            print("✅ 모든 Pinecone 데이터 삭제 완료")
        else:
            print("❌ 삭제 취소됨")
            
    except Exception as e:
        print(f"❌ 삭제 실패: {e}")

def debug_pinecone_data():
    """Pinecone 데이터 상세 진단"""
    
    print("\n" + "=" * 60)
    print("           Pinecone 데이터 진단")
    print("=" * 60)
    
    try:
        # 1. 전체 통계
        stats = index.describe_index_stats()
        print(f"📊 총 벡터 수: {stats.total_vector_count}")
        
        # 2. 네임스페이스별 상세 확인
        if stats.namespaces:
            for namespace, info in stats.namespaces.items():
                print(f"\n📋 네임스페이스: {namespace}")
                print(f"   벡터 수: {info.vector_count}개")
                
                # 각 네임스페이스에서 샘플 검색해보기
                sample_results = index.query(
                    vector=[0.1] * 1536,  # 더미 벡터로 검색
                    top_k=1,
                    namespace=namespace,
                    include_metadata=True
                )
                
                if sample_results.matches:
                    sample = sample_results.matches[0]
                    print(f"   샘플 메타데이터: {list(sample.metadata.keys())}")
                else:
                    print(f"   ⚠️ 검색 결과 없음")
        
        # 3. 실제 의미있는 검색 테스트
        print(f"\n🔍 실제 검색 테스트:")
        query_embedding = get_embedding("제1조")
        
        # law_articles 네임스페이스 검색
        law_results = index.query(
            vector=query_embedding,
            top_k=2,
            namespace="law_articles",
            include_metadata=True
        )
        print(f"law_articles 검색 결과: {len(law_results.matches)}개")
        
        # appendix_tables 네임스페이스 검색 
        try:
            star_results = index.query(
                vector=query_embedding,
                top_k=2,
                namespace="appendix_tables",
                include_metadata=True
            )
            print(f"appendix_tables 검색 결과: {len(star_results.matches)}개")
        except Exception as e:
            print(f"appendix_tables 검색 실패: {e}")
            
    except Exception as e:
        print(f"❌ 진단 실패: {e}")

def check_pinecone_indexes():
    """Pinecone 인덱스 상태 확인"""
    
    print("\n" + "=" * 60)
    print("           Pinecone 인덱스 상태 확인")
    print("=" * 60)
    
    try:
        # 1. 사용 가능한 인덱스 목록
        indexes = pc.list_indexes()
        print(f"📋 사용 가능한 인덱스 목록:")
        for idx in indexes:
            print(f"   - 이름: {idx.name}")
            print(f"     상태: {idx.status.state}")
            print(f"     호스트: {idx.host}")
            print(f"     차원: {idx.dimension}")
            print()
        
        # 2. 현재 연결된 인덱스 정보
        print(f"🔗 현재 사용 중인 인덱스: {index_name}")
        
        # 3. 인덱스 상세 정보
        if index_name in [idx.name for idx in indexes]:
            index_info = pc.describe_index(index_name)
            print(f"✅ 인덱스 상태: {index_info.status.state}")
            print(f"📍 호스트 URL: {index_info.host}")
            print(f"📏 벡터 차원: {index_info.dimension}")
            print(f"🏷️ 메트릭: {index_info.metric}")
            print(f"☁️ 클라우드: {index_info.spec.serverless.cloud}")
            print(f"🌍 지역: {index_info.spec.serverless.region}")
        else:
            print("❌ 인덱스를 찾을 수 없습니다!")
            
    except Exception as e:
        print(f"❌ 인덱스 확인 실패: {e}")

def list_all_namespaces():
    """모든 네임스페이스 목록 확인"""
    
    print("\n" + "=" * 60)
    print("           네임스페이스 목록 확인")
    print("=" * 60)
    
    try:
        stats = index.describe_index_stats()
        
        if stats.namespaces:
            print("📋 발견된 네임스페이스:")
            for namespace, info in stats.namespaces.items():
                print(f"   • '{namespace}': {info.vector_count}개 벡터")
                
                # 각 네임스페이스에서 샘플 데이터 가져오기
                try:
                    sample_query = index.query(
                        vector=[0.1] * 1536,
                        top_k=1,
                        namespace=namespace,
                        include_metadata=True
                    )
                    
                    if sample_query.matches:
                        sample = sample_query.matches[0]
                        print(f"     샘플 ID: {sample.id}")
                        print(f"     메타데이터 키: {list(sample.metadata.keys())}")
                        if 'law_article_id' in sample.metadata:
                            print(f"     조문: {sample.metadata.get('law_article_id')}")
                        if 'table_id' in sample.metadata:
                            print(f"     별표: {sample.metadata.get('table_id')}")
                    print()
                        
                except Exception as e:
                    print(f"     ⚠️ 샘플 조회 실패: {e}")
        else:
            print("❌ 네임스페이스를 찾을 수 없습니다.")
            
    except Exception as e:
        print(f"❌ 네임스페이스 확인 실패: {e}")

def show_menu():
    """메뉴 표시"""
    print("\n" + "🎯" * 30)
    print("           한라대학교 LLM 테스트 시스템")
    print("🎯" * 30)
    print()
    print("📋 테스트 옵션을 선택하세요:")
    print("   1. 전체 파이프라인 테스트 (PDF → 청크 → MongoDB → Pinecone)")
    print("   2. MongoDB 조회 테스트")
    print("   3. Pinecone 벡터 검색 테스트 ✨")
    print("   4. Pinecone 인덱스 통계")
    print("   5. 테스트 데이터 삭제 (MongoDB)")
    print("   6. 벡터 데이터 삭제 (Pinecone)")
    print("   7. Pinecone 벡터 업로드만 실행 (MongoDB에 있는 청크를 Pinecone으로 업로드)")
    print("   8. Pinecone 데이터 진단")
    print("   9. Pinecone 인덱스 상태 확인")
    print("   10. 네임스페이스 목록 확인")
    print("   0. 종료")
    print()

def main():
    """메인 실행 함수 - 무한 루프로 계속 테스트 가능"""
    
    print("🚀 한라대학교 LLM 시스템 테스트 환경에 오신 것을 환영합니다!")
    
    while True:
        try:
            show_menu()
            choice = input("👉 선택 (0-10): ").strip()
            
            if choice == "0":
                print("\n👋 테스트를 종료합니다. 수고하셨습니다!")
                break
            elif choice == "1":
                test_full_pipeline()
            elif choice == "2":
                test_mongodb_query()
            elif choice == "3":
                test_pinecone_vector_search()
            elif choice == "4":
                test_pinecone_stats()
            elif choice == "5":
                cleanup_test_data()
            elif choice == "6":
                cleanup_pinecone_data()
            elif choice == "7":
                # MongoDB에 저장된 청크만을 Pinecone으로 업로드하는 간단 실행 경로
                print("\n🚀 Pinecone 벡터 업로드 (MongoDB -> Pinecone) 시작")
                try:
                    upload_chunks_to_pinecone(category="law_articles")
                    upload_chunks_to_pinecone(category="appendix_tables")
                    print("✅ Pinecone 업로드 완료!")
                except Exception as e:
                    print(f"❌ Pinecone 업로드 실패: {e}")
            elif choice == "8":
                debug_pinecone_data()
            elif choice == "9":
                check_pinecone_indexes()
            elif choice == "10":
                list_all_namespaces()
            else:
                print("❌ 잘못된 선택입니다. 0-10 사이의 숫자를 입력해주세요.")
            
            # 작업 완료 후 사용자에게 계속할지 물어보기
            if choice != "0":
                print("\n" + "-" * 60)
                continue_choice = input("계속 테스트하시겠습니까? (Enter: 계속, q: 종료): ").strip().lower()
                if continue_choice == 'q':
                    print("\n👋 테스트를 종료합니다. 수고하셨습니다!")
                    break
                
        except KeyboardInterrupt:
            print("\n\n⚠️ Ctrl+C로 종료되었습니다.")
            break
        except Exception as e:
            print(f"\n❌ 예상치 못한 오류가 발생했습니다: {e}")
            print("계속 진행하거나 종료하시겠습니까?")

if __name__ == "__main__":
    main()

