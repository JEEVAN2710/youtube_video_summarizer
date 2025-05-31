# youtube_video_summarizer
![image](https://github.com/user-attachments/assets/6acbffb1-2d71-47ef-b5c9-6c19b1b7b8eb)
![image](https://github.com/user-attachments/assets/88e2d12c-d19d-4839-a9e0-6fa714f7e563)
![image](https://github.com/user-attachments/assets/c805454d-10ab-4390-9d84-049e48aaad53)

<div align="center">

# 🎬 YouTube Video Summarizer

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT-lightgrey)](https://openai.com/)
[![MIT License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

</div>

## 🧠 Overview

**YouTube Video Summarizer** is a Python-based tool that fetches the transcript of any public YouTube video and generates a concise summary using the power of OpenAI’s language models.

This tool is especially useful for students, researchers, content creators, and professionals who want quick insights from long-form video content like lectures, podcasts, and interviews.

---

## ✨ Features

* 🔗 Input any YouTube video URL
* 🧾 Fetches transcripts automatically using the YouTube Transcript API
* 💡 Summarizes video content using OpenAI's GPT models
* 🧠 Provides quick, easy-to-read summaries
* 💾 Optionally saves the output

---

## 🚀 Getting Started

### ✅ Prerequisites

* Python 3.8 or higher
* OpenAI API Key

## 🛠️ Installation

Follow these steps to set up the project on your local machine:

### 1. Clone the Repository

```bash
git clone https://github.com/JEEVAN2710/youtube_video_summarizer.git
cd youtube_video_summarizer
```

### 2. Create a Virtual Environment (Optional but Recommended)

```bash
python -m venv venv
source venv/bin/activate  # On Windows, use venv\Scripts\activate
```

### 3. Install Required Dependencies

```bash
pip install -r requirements.txt
```

### 4. Set Your OpenAI API Key

Make sure you have an OpenAI API key. Then export it as an environment variable:

```bash
export OPENAI_API_KEY="your-api-key-here"   # For Linux/macOS
```

On Windows CMD:

```cmd
set OPENAI_API_KEY="your-api-key-here"
```

On Windows PowerShell:

```powershell
$env:OPENAI_API_KEY="your-api-key-here"
```

✅ You're now ready to use the YouTube Video Summarizer!

---

## ▶️ Usage

Run the script via the command line:

```bash
python youtube_summarizer.py
```

You will be prompted to:

* Enter the YouTube video URL
* Wait for the transcript to be retrieved
* Receive a summarized output using OpenAI's API

---

## 📂 Example Output

```text
YouTube URL: https://www.youtube.com/watch?v=dQw4w9WgXcQ

Summary:
The video covers key aspects of motivation and productivity, 
emphasizing practical strategies like time-blocking and habit-building.
```

---

## 🧪 Tech Stack

| Component        | Technology                   |
| ---------------- | ---------------------------- |
| Backend Script   | Python                       |
| Transcript Fetch | youtube-transcript-api       |
| CLI UI           | Rich (optional, for styling) |

---

## 🚧 Roadmap / Future Improvements

* [ ] Add GUI using Streamlit or Gradio
* [ ] Download support for non-transcript videos
* [ ] Export summaries to PDF or Markdown

---

## 🤝 Contributing

Contributions are welcome! You can fix this repo and submit a pull request with improvements or bug fixes.

If you find any issues, please [open an issue](https://github.com/JEEVAN2710/youtube_video_summarizer/issues).

---

## DEMO PHOTO



* [youtube-transcript-api](https://github.com/jdepoix/youtube-transcript-api) for transcript support
* Made with ❤️ by [JEEVAN2710](https://github.com/JEEVAN2710)
