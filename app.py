import gradio as gr
import whisper
import subprocess
import tempfile
import os

# Whisper 모델 로드
print("Loading Whisper model...")
model = whisper.load_model("base")
print("Model loaded!")

def download_youtube(url):
    """yt-dlp로 유튜브 다운로드"""
    try:
        output_path = tempfile.mktemp(suffix='.mp4')
        cmd = [
            'yt-dlp',
            '-f', 'best[ext=mp4]',
            '-o', output_path,
            url
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode != 0:
            raise Exception(f"다운로드 실패: {result.stderr[:200]}")
        return output_path
    except Exception as e:
        raise Exception(f"유튜브 다운로드 오류: {str(e)}")

def extract_audio(video_path):
    """비디오에서 오디오 추출"""
    audio_path = tempfile.mktemp(suffix='.wav')
    cmd = [
        'ffmpeg', '-i', video_path,
        '-vn', '-acodec', 'pcm_s16le',
        '-ar', '16000', '-ac', '1',
        '-y', audio_path
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    return audio_path

def format_timestamp(seconds):
    """초를 HH:MM:SS 형식으로"""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    return f"{h:02d}:{m:02d}:{s:02d}"

def process_youtube(url, language):
    """유튜브 처리"""
    video_path = None
    audio_path = None
    
    try:
        if not url or not url.strip():
            return "❌ 유튜브 URL을 입력해주세요.", ""
        
        # 다운로드
        video_path = download_youtube(url.strip())
        
        # 오디오 추출
        audio_path = extract_audio(video_path)
        
        # 음성 인식
        lang = None if language == "자동 감지" else language.lower()[:2]
        result = model.transcribe(audio_path, language=lang, verbose=False)
        
        # 정리
        if video_path and os.path.exists(video_path):
            os.remove(video_path)
        if audio_path and os.path.exists(audio_path):
            os.remove(audio_path)
        
        # 결과
        full_text = result['text'].strip()
        
        timestamped = ""
        for seg in result['segments']:
            start = format_timestamp(seg['start'])
            end = format_timestamp(seg['end'])
            text = seg['text'].strip()
            timestamped += f"[{start} → {end}]\n{text}\n\n"
        
        return f"✅ 완료!\n\n{full_text}", timestamped
        
    except Exception as e:
        # 정리
        if video_path and os.path.exists(video_path):
            os.remove(video_path)
        if audio_path and os.path.exists(audio_path):
            os.remove(audio_path)
        return f"❌ 에러: {str(e)}", ""

def process_file(file, language):
    """파일 처리"""
    audio_path = None
    
    try:
        if file is None:
            return "❌ 파일을 업로드해주세요.", ""
        
        # 오디오 추출
        audio_path = extract_audio(file.name)
        
        # 음성 인식
        lang = None if language == "자동 감지" else language.lower()[:2]
        result = model.transcribe(audio_path, language=lang, verbose=False)
        
        # 정리
        if audio_path and os.path.exists(audio_path):
            os.remove(audio_path)
        
        # 결과
        full_text = result['text'].strip()
        
        timestamped = ""
        for seg in result['segments']:
            start = format_timestamp(seg['start'])
            end = format_timestamp(seg['end'])
            text = seg['text'].strip()
            timestamped += f"[{start} → {end}]\n{text}\n\n"
        
        return f"✅ 완료!\n\n{full_text}", timestamped
        
    except Exception as e:
        if audio_path and os.path.exists(audio_path):
            os.remove(audio_path)
        return f"❌ 에러: {str(e)}", ""

# UI - Gradio 3.x 스타일
with gr.Blocks(title="영상 스크립트 추출기") as demo:
    
    gr.Markdown("# 🎬 영상 → 스크립트 변환기")
    gr.Markdown("유튜브 링크나 영상 파일에서 음성을 텍스트로 변환합니다")
    
    with gr.Tab("🎥 유튜브"):
        gr.Markdown("### 유튜브 영상 URL 입력")
        yt_url = gr.Textbox(label="유튜브 URL", placeholder="https://www.youtube.com/watch?v=...")
        yt_lang = gr.Radio(
            choices=["한국어", "영어", "일본어", "중국어", "자동 감지"],
            value="한국어",
            label="언어"
        )
        yt_btn = gr.Button("🚀 스크립트 추출 시작")
        
        gr.Markdown("### 결과")
        yt_output1 = gr.Textbox(label="📝 전체 스크립트", lines=12)
        yt_output2 = gr.Textbox(label="⏱️ 타임스탬프", lines=12)
        
        yt_btn.click(
            fn=process_youtube,
            inputs=[yt_url, yt_lang],
            outputs=[yt_output1, yt_output2]
        )
    
    with gr.Tab("📁 파일 업로드"):
        gr.Markdown("### 영상 파일 업로드")
        file_input = gr.File(label="영상 파일 (MP4, AVI, MOV 등)")
        file_lang = gr.Radio(
            choices=["한국어", "영어", "일본어", "중국어", "자동 감지"],
            value="한국어",
            label="언어"
        )
        file_btn = gr.Button("🚀 스크립트 추출 시작")
        
        gr.Markdown("### 결과")
        file_output1 = gr.Textbox(label="📝 전체 스크립트", lines=12)
        file_output2 = gr.Textbox(label="⏱️ 타임스탬프", lines=12)
        
        file_btn.click(
            fn=process_file,
            inputs=[file_input, file_lang],
            outputs=[file_output1, file_output2]
        )
    
    gr.Markdown("""
    ---
    ### 💡 사용 팁
    
    - **처리 시간**: 10분 영상 기준 약 2-5분 소요
    - **유튜브**: 공개된 영상만 가능
    - **파일**: MP4, AVI, MOV, MKV 등 지원
    - **정확도**: 배경 소음이 적고 발음이 명확할수록 좋아요
    
    Made with ❤️ using OpenAI Whisper & Gradio
    """)

demo.launch()
