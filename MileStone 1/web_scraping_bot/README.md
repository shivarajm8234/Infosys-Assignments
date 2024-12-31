# Intelligent Web Scraping Bot

An advanced web scraping application that combines web scraping capabilities with natural language processing to provide an interactive chat interface for extracting and analyzing web content.

## Problem Statement

Traditional web scraping tools often provide raw data that requires additional processing and analysis. Users need a more intuitive way to:
1. Extract content from websites
2. Ask questions about the scraped content
3. Get meaningful insights from the data
4. Interact with the scraping tool in a natural way

## Features

- 🌐 **Intelligent Web Scraping**
  - Extracts structured content from any website
  - Handles dynamic content and different HTML structures
  - Supports various content types (text, links, headings)

- 💬 **Interactive Chat Interface**
  - Natural language interaction
  - Ask questions about scraped content
  - Get contextual responses

- 🎨 **Modern UI/UX**
  - Clean and responsive design
  - Dark/Light mode toggle
  - Loading indicators and animations
  - User-friendly error messages

- 🔍 **Content Analysis**
  - Automatic content summarization
  - Structured content presentation
  - Link extraction and organization

## Technical Requirements

### Backend Dependencies
```
flask>=3.0.0
requests>=2.31.0
beautifulsoup4>=4.12.2
aiohttp>=3.9.1
pandas>=2.1.4
rich>=13.7.0
openpyxl>=3.1.2
transformers>=4.36.0
torch>=2.1.0
nest_asyncio>=1.5.8
brotli==1.1.0
brotlipy==0.7.0
```

### Frontend Technologies
- HTML5
- CSS3 (with Tailwind CSS)
- JavaScript (ES6+)
- Font Awesome Icons
- Google Fonts (Inter)

## Architecture

### Components

1. **Web Scraping Module (`scraper.py`)**
   - Handles website content extraction
   - Manages HTTP sessions and requests
   - Processes HTML content

2. **Chat Bot Module (`web_scraping_bot.py`)**
   - Processes user queries
   - Manages conversation context
   - Generates responses

3. **Flask Server (`app.py`)**
   - Handles HTTP routes
   - Manages API endpoints
   - Coordinates between frontend and backend

4. **Frontend Interface (`templates/index.html`)**
   - User interface components
   - Real-time updates
   - Interactive features

### Implementation Approach

1. **Web Scraping Strategy**
   - Asynchronous requests for better performance
   - Robust error handling
   - Content extraction based on HTML structure
   - Support for compressed responses (brotli)

2. **Natural Language Processing**
   - Query understanding
   - Context maintenance
   - Relevant response generation

3. **User Interface Design**
   - Mobile-first responsive design
   - Intuitive chat interface
   - Clear visual feedback
   - Accessibility considerations

## Setup and Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd web_scraping_bot
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run the application:
   ```bash
   python app.py
   ```

5. Access the application:
   Open `http://localhost:5000` in your web browser

## Usage

1. **Scraping Content**
   - Enter a URL in the input field
   - Click "Scrape" or press Enter
   - Wait for content to be extracted

2. **Asking Questions**
   - Type your question in the chat input
   - Click "Send" or press Enter
   - View the AI's response

3. **Viewing Content**
   - Extracted content appears in the right panel
   - Content is organized by type (headings, paragraphs, links)
   - Use the summary section for quick overview

## Future Enhancements

1. **Advanced Features**
   - PDF export functionality
   - Multi-language support
   - Custom scraping rules
   - Data visualization

2. **Technical Improvements**
   - Caching mechanism
   - Rate limiting
   - Advanced error recovery
   - Session management

3. **UI Enhancements**
   - More theme options
   - Customizable layout
   - Advanced search features
   - Voice interaction

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
![Screenshot from 2024-12-26 00-39-10](https://github.com/user-attachments/assets/ee1776ce-5bc6-45d1-a1b0-4f7d83d24419)
------------------------------------------------------------------------------------------------------------------------
https://github.com/user-attachments/assets/4ac3661e-7548-498d-b1eb-ba99d03bc674


## License

This project is licensed under the MIT License - see the LICENSE file for details.
