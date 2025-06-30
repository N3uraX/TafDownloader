# TafDownloader - Setup Instructions

## Quick Start

### Backend Setup
```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend Setup
```bash
npm install
npm run dev
```

## Current Status

### ✅ Fully Working Platforms
- **Twitter/X**: All URL formats supported
- **Instagram**: Posts and stories
- **TikTok**: Video downloads
- **Facebook**: Public videos
- **Other platforms**: Most video platforms work normally

### ⚠️ YouTube Status
- **Current Issue**: YouTube has implemented aggressive bot detection (January 2025)
- **User Experience**: Clear error messages explain the temporary limitation
- **Technical**: Multiple bypass strategies implemented, may work intermittently
- **Recommendation**: Users are guided to try other platforms

## Features Implemented

### Enhanced YouTube Handling
- **9 Different Client Strategies**: Android, iOS, Web, TV, Music variants
- **Browser Cookie Integration**: Automatic detection from Chrome, Firefox, Safari, Edge
- **Rate Limiting**: Built-in delays to avoid triggering restrictions
- **Fallback Chain**: Sequential attempt of different extraction methods

### Improved User Experience
- **Clear Error Messages**: User-friendly explanations instead of technical errors
- **Appropriate HTTP Codes**: 503 for temporary issues, 429 for rate limits
- **Platform Detection**: Better recognition of video sources
- **URL Normalization**: Handles various YouTube URL formats

### Technical Improvements
- **Modern User Agents**: Up-to-date browser user agents
- **Better Quality Detection**: Improved format filtering and selection
- **Error Recovery**: Graceful degradation when primary methods fail
- **Logging**: Comprehensive logging for debugging

## Configuration

### Environment Variables
- `YTDLP_PROXY`: Optional proxy for yt-dlp requests
- `VITE_API_URL`: Frontend API URL (default: http://localhost:8000/api)

### Optional: FFmpeg Setup
For video processing on Windows:
```bash
# Install via Chocolatey
choco install ffmpeg
```

## Troubleshooting

### YouTube Videos
If YouTube videos fail:
1. This is expected due to current platform restrictions
2. Users see clear error messages explaining the situation
3. Try different YouTube videos (some may work during low-restriction periods)
4. Consider using other video platforms

### Other Platforms
If other platforms fail:
1. Check the URL format
2. Verify the video is publicly accessible
3. Check server logs for specific error details
4. Try again after a short delay

## Development

### Adding New Platforms
1. Update `detectPlatform()` in `src/utils/videoUtils.ts`
2. Add platform-specific handling in `backend/main.py`
3. Test with various URL formats

### Improving YouTube Support
1. Monitor yt-dlp updates for new client strategies
2. Implement additional cookie sources
3. Add user-provided cookie upload feature
4. Consider proxy rotation

## API Endpoints

### POST /api/metadata
Extract video information
```json
{
  "url": "https://twitter.com/user/status/123456789"
}
```

### POST /api/download
Download video file
```json
{
  "url": "https://twitter.com/user/status/123456789",
  "quality": "720"
}
```

## Security Notes

- CORS is currently open for development (`allow_origins=["*"]`)
- In production, restrict CORS to your domain
- Consider rate limiting at the server level
- Monitor for abuse and implement user-based rate limiting

## Future Improvements

### Short Term
- User feedback collection system
- Better error reporting and analytics
- A/B testing of YouTube strategies

### Medium Term
- User-provided cookie upload
- Premium features with higher success rates
- API rate limiting per user

### Long Term
- Official API partnerships
- Desktop application with browser automation
- Focus expansion to other video platforms