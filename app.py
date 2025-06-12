import streamlit as st
from youtube_transcript_api import YouTubeTranscriptApi
from transformers import pipeline
import nltk
import os
import warnings
import requests
from bs4 import BeautifulSoup
import re

# Suppress warnings
warnings.filterwarnings("ignore")

# Download necessary NLTK resources
@st.cache_resource
def download_nltk_data():
    try:
        nltk.download('punkt', quiet=True)
        nltk.download('stopwords', quiet=True)
    except Exception as e:
        st.warning(f"Could not download NLTK data: {e}")

# Initialize the summarization model
@st.cache_resource
def load_summarizer():
    try:
        return pipeline("summarization", model="facebook/bart-large-cnn")
    except Exception as e:
        st.error(f"Could not load summarization model: {e}")
        return None

# Function to extract video ID from URL
def extract_video_id(url):
    """Extract video ID from various YouTube URL formats"""
    if not url:
        return None
    
    # Remove whitespace
    url = url.strip()
    
    # Handle different YouTube URL formats
    if "youtube.com/watch?v=" in url:
        video_id = url.split("youtube.com/watch?v=")[1].split("&")[0]
    elif "youtu.be/" in url:
        video_id = url.split("youtu.be/")[1].split("?")[0]
    elif "youtube.com/embed/" in url:
        video_id = url.split("youtube.com/embed/")[1].split("?")[0]
    else:
        # Assume it's already a video ID
        video_id = url
    
    return video_id

# Function to get video metadata
def get_video_info(video_id):
    """Get basic video information"""
    try:
        url = f"https://www.youtube.com/watch?v={video_id}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Try to extract title
            title_tag = soup.find('meta', property='og:title')
            title = title_tag['content'] if title_tag else "Unknown Title"
            
            # Try to extract description
            desc_tag = soup.find('meta', property='og:description')
            description = desc_tag['content'] if desc_tag else "No description available"
            
            return {
                'title': title,
                'description': description,
                'url': url
            }
    except Exception as e:
        return {
            'title': 'Unknown Title',
            'description': 'Could not fetch video information',
            'url': f"https://www.youtube.com/watch?v={video_id}"
        }

# Function to check available transcript languages
def get_available_transcripts(video_id):
    """Get list of available transcript languages"""
    try:
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        available_languages = []
        
        for transcript in transcript_list:
            lang_info = {
                'language': transcript.language,
                'language_code': transcript.language_code,
                'is_generated': transcript.is_generated,
                'is_translatable': transcript.is_translatable
            }
            available_languages.append(lang_info)
        
        return available_languages
    except Exception as e:
        return []

# Enhanced function to fetch transcript with multiple language support
def get_transcript_with_fallback(video_id):
    """Try to get transcript in multiple languages with fallback options"""
    try:
        # First, try to get available transcripts
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        
        # Priority order: English -> Auto-generated English -> Any English variant -> Any language
        language_priority = ['en', 'en-US', 'en-GB', 'en-CA', 'en-AU']
        
        # Try manual transcripts first
        for lang_code in language_priority:
            try:
                transcript = transcript_list.find_manually_created_transcript([lang_code])
                return transcript.fetch(), f"Manual transcript ({lang_code})"
            except:
                continue
        
        # Try auto-generated transcripts
        for lang_code in language_priority:
            try:
                transcript = transcript_list.find_generated_transcript([lang_code])
                return transcript.fetch(), f"Auto-generated transcript ({lang_code})"
            except:
                continue
        
        # Try any available transcript
        try:
            transcript = transcript_list.find_transcript(['en'])
            return transcript.fetch(), "English transcript"
        except:
            pass
        
        # Last resort: try any available language
        for transcript in transcript_list:
            try:
                if transcript.is_translatable:
                    # Try to translate to English
                    translated = transcript.translate('en')
                    return translated.fetch(), f"Translated from {transcript.language} to English"
                else:
                    return transcript.fetch(), f"Original transcript in {transcript.language}"
            except:
                continue
        
        return None, "No transcript available"
        
    except Exception as e:
        return None, f"Error: {str(e)}"

# Function to fetch and summarize YouTube video transcript
def summarize_youtube_video(video_id, summarizer, max_length=150, min_length=50):
    """Fetch transcript and generate summary with enhanced error handling"""
    try:
        # Get video info first
        video_info = get_video_info(video_id)
        
        # Try to get transcript with fallback
        transcript_data, transcript_source = get_transcript_with_fallback(video_id)
        
        if transcript_data is None:
            # If no transcript available, provide helpful information
            available_transcripts = get_available_transcripts(video_id)
            
            error_msg = "❌ **No transcript available for this video.**\n\n"
            error_msg += "**Possible reasons:**\n"
            error_msg += "• Subtitles/captions are disabled for this video\n"
            error_msg += "• The video is too new (transcripts may not be processed yet)\n"
            error_msg += "• The video is private or restricted\n"
            error_msg += "• The content creator hasn't enabled captions\n\n"
            
            if available_transcripts:
                error_msg += "**Available transcript languages:**\n"
                for lang in available_transcripts:
                    status = "Auto-generated" if lang['is_generated'] else "Manual"
                    error_msg += f"• {lang['language']} ({lang['language_code']}) - {status}\n"
            else:
                error_msg += "**No transcripts found in any language.**\n"
            
            error_msg += "\n**Suggestions:**\n"
            error_msg += "• Try a different video with captions enabled\n"
            error_msg += "• Check if the video has auto-generated captions\n"
            error_msg += "• Contact the video creator to enable captions\n"
            
            return error_msg, video_info, transcript_source
        
        # Combine all transcript text
        full_text = " ".join([entry['text'] for entry in transcript_data])
        
        if len(full_text.strip()) == 0:
            return "Transcript is empty.", video_info, transcript_source
        
        # Clean the text
        full_text = re.sub(r'\[.*?\]', '', full_text)  # Remove [Music], [Applause], etc.
        full_text = re.sub(r'\s+', ' ', full_text).strip()  # Clean whitespace
        
        # Handle long transcripts by chunking
        max_chunk_length = 1024  # BART model limit
        chunks = []
        
        # Split text into chunks
        words = full_text.split()
        current_chunk = []
        current_length = 0
        
        for word in words:
            if current_length + len(word) + 1 > max_chunk_length:
                if current_chunk:
                    chunks.append(" ".join(current_chunk))
                current_chunk = [word]
                current_length = len(word)
            else:
                current_chunk.append(word)
                current_length += len(word) + 1
        
        if current_chunk:
            chunks.append(" ".join(current_chunk))
        
        # Summarize each chunk
        summaries = []
        progress_bar = st.progress(0)
        
        for i, chunk in enumerate(chunks):
            try:
                if len(chunk.strip()) < 50:  # Skip very short chunks
                    continue
                    
                summary = summarizer(
                    chunk, 
                    max_length=max_length, 
                    min_length=min_length, 
                    do_sample=False
                )[0]['summary_text']
                summaries.append(summary)
                
                # Update progress
                progress_bar.progress((i + 1) / len(chunks))
                    
            except Exception as e:
                st.warning(f"Could not summarize chunk {i+1}: {e}")
                continue
        
        progress_bar.empty()
        
        if not summaries:
            return "Could not generate summary from the transcript.", video_info, transcript_source
        
        # Combine summaries
        final_summary = " ".join(summaries)
        
        # If we have multiple summaries, try to summarize them again
        if len(summaries) > 1 and len(final_summary) > max_chunk_length:
            try:
                final_summary = summarizer(
                    final_summary, 
                    max_length=max_length * 2, 
                    min_length=min_length, 
                    do_sample=False
                )[0]['summary_text']
            except Exception as e:
                st.warning(f"Could not create final summary: {e}")
        
        return final_summary, video_info, transcript_source
        
    except Exception as e:
        error_msg = str(e)
        video_info = get_video_info(video_id)
        
        if "No transcript found" in error_msg or "Subtitles are disabled" in error_msg:
            detailed_error = "❌ **Transcript not available**\n\n"
            detailed_error += "This video doesn't have subtitles/captions enabled. "
            detailed_error += "YouTube's transcript API can only work with videos that have:\n"
            detailed_error += "• Manual captions added by the creator\n"
            detailed_error += "• Auto-generated captions (available for most English videos)\n\n"
            detailed_error += "**Try these alternatives:**\n"
            detailed_error += "• Look for similar videos with captions enabled\n"
            detailed_error += "• Check if the video has community-contributed captions\n"
            detailed_error += "• Use videos from educational channels (they usually have captions)"
            return detailed_error, video_info, "No transcript"
        elif "Video unavailable" in error_msg:
            return "❌ **Video is unavailable, private, or restricted.**", video_info, "No access"
        else:
            return f"❌ **Error processing video:** {error_msg}", video_info, "Error"

# Streamlit App Configuration
st.set_page_config(
    page_title="YouTube Video Summarizer",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(90deg, #ff6b6b, #4ecdc4);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-size: 3rem;
        font-weight: bold;
        margin-bottom: 2rem;
    }
    
    .description {
        text-align: center;
        font-size: 1.2rem;
        color: #666;
        margin-bottom: 3rem;
    }
    
    .summary-box {
        background-color: #f8f9fa;
        padding: 2rem;
        border-radius: 10px;
        border-left: 5px solid #4ecdc4;
        margin: 2rem 0;
    }
    
    .error-box {
        background-color: #fff5f5;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 5px solid #ff6b6b;
        color: #c53030;
        margin: 2rem 0;
    }
    
    .info-box {
        background-color: #f0f8ff;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 5px solid #4169e1;
        margin: 1rem 0;
    }
    
    .video-info {
        background-color: #f9f9f9;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Main App
def main():
    # Header
    st.markdown('<h1 class="main-header">🎬 YouTube Video Summarizer</h1>', unsafe_allow_html=True)
    st.markdown('<p class="description">Enter a YouTube video URL to get an AI-powered summary of its content</p>', unsafe_allow_html=True)
    
    # Important notice
    st.markdown("""
    <div class="info-box">
        <h4>📋 Important Notes:</h4>
        <ul>
            <li>This tool only works with videos that have <strong>captions/subtitles enabled</strong></li>
            <li>Most educational and popular videos have auto-generated captions</li>
            <li>If a video doesn't work, try another video with captions</li>
            <li>Processing time depends on video length (longer videos take more time)</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize components
    download_nltk_data()
    summarizer = load_summarizer()
    
    if summarizer is None:
        st.error("Failed to load the summarization model. Please refresh the page.")
        return
    
    # Input section
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        video_url = st.text_input(
            "YouTube Video URL or ID:",
            placeholder="https://www.youtube.com/watch?v=...",
            help="Paste any YouTube video URL or just the video ID"
        )
        
        # Advanced options
        with st.expander("⚙️ Advanced Options"):
            col_a, col_b = st.columns(2)
            with col_a:
                max_length = st.slider("Max Summary Length", 100, 300, 150)
            with col_b:
                min_length = st.slider("Min Summary Length", 30, 100, 50)
    
    # Example videos section
    st.markdown("---")
    st.subheader("🎯 Try These Example Videos (Known to Have Captions)")
    
    example_videos = [
        ("TED Talk: The Power of Vulnerability", "https://www.youtube.com/watch?v=iCvmsMzlF7o"),
        ("Khan Academy: Introduction to Algebra", "https://www.youtube.com/watch?v=NybHckSEQBI"),
        ("Crash Course: World History", "https://www.youtube.com/watch?v=Yocja_N5s1I"),
    ]
    
    cols = st.columns(len(example_videos))
    for i, (title, url) in enumerate(example_videos):
        with cols[i]:
            if st.button(f"📺 {title}", key=f"example_{i}"):
                st.session_state.example_url = url
                st.rerun()
    
    # Use example URL if selected
    if hasattr(st.session_state, 'example_url'):
        video_url = st.session_state.example_url
        st.info(f"Using example video: {video_url}")
    
    # Process button
    if st.button("🚀 Generate Summary", type="primary", use_container_width=True):
        if not video_url:
            st.warning("Please enter a YouTube video URL or ID.")
            return
        
        video_id = extract_video_id(video_url)
        
        if not video_id:
            st.error("Invalid YouTube URL or video ID.")
            return
        
        # Show video info
        st.markdown("---")
        st.subheader("📹 Video Information")
        
        # Generate summary
        with st.spinner("🔍 Checking video and fetching transcript... This may take a moment."):
            result, video_info, transcript_source = summarize_youtube_video(video_id, summarizer, max_length, min_length)
        
        # Display video information
        st.markdown(f"""
        <div class="video-info">
            <h4>📺 {video_info['title']}</h4>
            <p><strong>Description:</strong> {video_info['description'][:200]}{'...' if len(video_info['description']) > 200 else ''}</p>
            <p><strong>Transcript Source:</strong> {transcript_source}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Embed video
        try:
            st.video(f"https://www.youtube.com/watch?v={video_id}")
        except Exception as e:
            st.warning("Could not embed video preview.")
        
        # Display results
        st.subheader("📝 Summary")
        
        if result.startswith("❌"):
            st.markdown(f'<div class="error-box">{result}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="summary-box"><h4>✅ Summary Generated Successfully:</h4><p>{result}</p></div>', unsafe_allow_html=True)
            
            # Download option
            st.download_button(
                label="📥 Download Summary",
                data=f"Video: {video_info['title']}\nURL: {video_info['url']}\nTranscript Source: {transcript_source}\n\nSummary:\n{result}",
                file_name=f"youtube_summary_{video_id}.txt",
                mime="text/plain"
            )

# Sidebar
with st.sidebar:
    st.markdown("### 📖 About")
    st.markdown("""
    This tool uses AI to automatically generate summaries of YouTube videos by analyzing their transcripts.
    
    **✨ Features:**
    - 🎯 Automatic transcript extraction
    - 🤖 AI-powered summarization using BART
    - 🌍 Multi-language transcript support
    - 📱 Mobile-friendly interface
    - 💾 Download summaries
    - 🔄 Fallback transcript options
    
    **📋 Requirements:**
    - Videos must have captions/subtitles enabled
    - Works with auto-generated or manual captions
    - Supports multiple languages (auto-translates to English)
    - Public videos only
    """)
    
    st.markdown("---")
    st.markdown("### 🛠️ Troubleshooting")
    st.markdown("""
    **If you get an error:**
    1. ✅ Check if the video has captions enabled
    2. 🔄 Try a different video
    3. 📺 Use educational/popular channels (they usually have captions)
    4. ⏰ Wait a few minutes for new videos (captions may be processing)
    """)
    
    st.markdown("---")
    st.markdown("Made with ❤️ using Streamlit & Transformers")

if __name__ == "__main__":
    main()