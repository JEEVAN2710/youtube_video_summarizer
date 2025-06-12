import streamlit as st
from youtube_transcript_api import YouTubeTranscriptApi
from transformers import pipeline
import nltk
import os
import warnings

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

# Function to fetch and summarize YouTube video transcript
def summarize_youtube_video(video_id, summarizer, max_length=150, min_length=50):
    """Fetch transcript and generate summary"""
    try:
        # Get transcript
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        
        if not transcript:
            return "No transcript available for this video."
        
        # Combine all transcript text
        full_text = " ".join([entry['text'] for entry in transcript])
        
        if len(full_text.strip()) == 0:
            return "Transcript is empty."
        
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
                
                # Show progress for long videos
                if len(chunks) > 1:
                    st.progress((i + 1) / len(chunks))
                    
            except Exception as e:
                st.warning(f"Could not summarize chunk {i+1}: {e}")
                continue
        
        if not summaries:
            return "Could not generate summary from the transcript."
        
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
        
        return final_summary
        
    except Exception as e:
        error_msg = str(e)
        if "No transcript found" in error_msg:
            return "No transcript available for this video. The video might not have captions enabled."
        elif "Video unavailable" in error_msg:
            return "Video is unavailable or private."
        else:
            return f"Error processing video: {error_msg}"

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
        padding: 1rem;
        border-radius: 5px;
        border-left: 5px solid #ff6b6b;
        color: #c53030;
    }
</style>
""", unsafe_allow_html=True)

# Main App
def main():
    # Header
    st.markdown('<h1 class="main-header">🎬 YouTube Video Summarizer</h1>', unsafe_allow_html=True)
    st.markdown('<p class="description">Enter a YouTube video URL to get an AI-powered summary of its content</p>', unsafe_allow_html=True)
    
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
        with st.expander("Advanced Options"):
            col_a, col_b = st.columns(2)
            with col_a:
                max_length = st.slider("Max Summary Length", 100, 300, 150)
            with col_b:
                min_length = st.slider("Min Summary Length", 30, 100, 50)
    
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
        
        # Embed video
        try:
            st.video(f"https://www.youtube.com/watch?v={video_id}")
        except Exception as e:
            st.warning("Could not embed video preview.")
        
        # Generate summary
        st.subheader("📝 Summary")
        
        with st.spinner("Fetching transcript and generating summary... This may take a moment."):
            summary = summarize_youtube_video(video_id, summarizer, max_length, min_length)
        
        # Display results
        if summary.startswith("Error") or summary.startswith("No transcript") or summary.startswith("Video is unavailable"):
            st.markdown(f'<div class="error-box">{summary}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="summary-box"><h4>Summary:</h4><p>{summary}</p></div>', unsafe_allow_html=True)
            
            # Download option
            st.download_button(
                label="📥 Download Summary",
                data=summary,
                file_name=f"youtube_summary_{video_id}.txt",
                mime="text/plain"
            )

# Sidebar
with st.sidebar:
    st.markdown("### About")
    st.markdown("""
    This tool uses AI to automatically generate summaries of YouTube videos by analyzing their transcripts.
    
    **Features:**
    - 🎯 Automatic transcript extraction
    - 🤖 AI-powered summarization
    - 📱 Mobile-friendly interface
    - 💾 Download summaries
    
    **Supported Videos:**
    - Videos with auto-generated captions
    - Videos with manual captions
    - Public videos only
    """)
    
    st.markdown("---")
    st.markdown("Made with ❤️ using Streamlit")

if __name__ == "__main__":
    main()