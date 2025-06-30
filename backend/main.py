from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import yt_dlp
import os
import random
import time
import logging
from typing import Optional, Dict, Any
import asyncio
from concurrent.futures import ThreadPoolExecutor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure FFmpeg paths for Windows
if os.name == 'nt':  # Windows
    ffmpeg_paths = [
        r"C:\ProgramData\chocolatey\bin",
        r"C:\ProgramData\chocolatey\lib\ffmpeg\tools\ffmpeg\bin"
    ]
    os.environ["PATH"] = os.pathsep.join(ffmpeg_paths + os.environ["PATH"].split(os.pathsep))

app = FastAPI()

# Read proxy from environment variable
YTDLP_PROXY = os.getenv("YTDLP_PROXY")

# Allow CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change this in production!
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modern realistic user agents for better bot detection evasion
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.2 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:133.0) Gecko/20100101 Firefox/133.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0"
]

# YouTube extractor configurations for different client strategies
YOUTUBE_CONFIGS = [
    # Strategy 1: Android Test Suite - often bypasses restrictions
    {
        "name": "ANDROID_TESTSUITE",
        "extractor_args": {
            "youtube": {
                "player_client": ["android_testsuite"],
                "player_skip": ["webpage"],
            }
        },
        "http_headers": {
            "User-Agent": "com.google.android.youtube/17.36.4 (Linux; U; Android 11) gzip"
        }
    },
    # Strategy 2: Android VR - less detected
    {
        "name": "ANDROID_VR",
        "extractor_args": {
            "youtube": {
                "player_client": ["android_vr"],
                "player_skip": ["webpage"],
            }
        },
        "http_headers": {
            "User-Agent": "com.google.android.apps.youtube.vr.oculus/1.37.0 (Linux; U; Android 8.1.0; Oculus Quest) gzip"
        }
    },
    # Strategy 3: Web Music Analytics - alternative client  
    {
        "name": "WEB_MUSIC_ANALYTICS",
        "extractor_args": {
            "youtube": {
                "player_client": ["web_music_analytics"],
                "player_skip": ["webpage"],
            }
        },
        "http_headers": {
            "User-Agent": random.choice(USER_AGENTS),
            "Origin": "https://music.youtube.com",
            "Referer": "https://music.youtube.com/"
        }
    },
    # Strategy 4: Android Music - often has fewer restrictions
    {
        "name": "ANDROID_MUSIC", 
        "extractor_args": {
            "youtube": {
                "player_client": ["android_music"],
                "player_skip": ["webpage"],
            }
        },
        "http_headers": {
            "User-Agent": "com.google.android.apps.youtube.music/5.26.1 (Linux; U; Android 11) gzip"
        }
    },
    # Strategy 5: iOS Music - alternative iOS client
    {
        "name": "IOS_MUSIC",
        "extractor_args": {
            "youtube": {
                "player_client": ["ios_music"],
                "player_skip": ["webpage"],
            }
        },
        "http_headers": {
            "User-Agent": "com.google.ios.youtubemusic/5.26.1 (iPhone14,3; U; CPU iOS 15_6 like Mac OS X)"
        }
    },
    # Strategy 6: TV HTML5 Embedded - often bypasses age restrictions
    {
        "name": "TVHTML5_EMBEDDED",
        "extractor_args": {
            "youtube": {
                "player_client": ["tv_embedded"],
                "player_skip": ["webpage"],
            }
        },
        "http_headers": {
            "User-Agent": "Mozilla/5.0 (SMART-TV; LINUX; Tizen 6.0) AppleWebKit/537.36 (KHTML, like Gecko) 85.0.4183.93/6.0 TV Safari/537.36",
            "Origin": "https://www.youtube.com",
            "Referer": "https://www.youtube.com/"
        }
    },
    # Strategy 7: Standard Android with different version
    {
        "name": "ANDROID",
        "extractor_args": {
            "youtube": {
                "player_client": ["android"],
                "player_skip": ["webpage"],
            }
        },
        "http_headers": {
            "User-Agent": "com.google.android.youtube/17.36.4 (Linux; U; Android 11) gzip"
        }
    },
    # Strategy 8: iOS client
    {
        "name": "IOS",
        "extractor_args": {
            "youtube": {
                "player_client": ["ios"],
                "player_skip": ["webpage"],
            }
        },
        "http_headers": {
            "User-Agent": "com.google.ios.youtube/17.36.4 (iPhone14,3; U; CPU iOS 15_6 like Mac OS X)"
        }
    },
    # Strategy 9: Web client with enhanced headers - fallback
    {
        "name": "WEB_ENHANCED",
        "extractor_args": {
            "youtube": {
                "player_client": ["web"],
                "player_skip": ["configs", "webpage"],
            }
        },
        "http_headers": {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Cache-Control": "max-age=0"
        }
    }
]

def get_base_ydl_opts(proxy: Optional[str] = None) -> Dict[str, Any]:
    """Get base yt-dlp options with enhanced bot detection evasion"""
    opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": False,
        "writethumbnail": False,
        "writeinfojson": False,
        "ignoreerrors": False,
        "sleep_interval": random.uniform(0.5, 2),
        "max_sleep_interval": 4,
        "socket_timeout": 30,
        "retries": 2,
        "fragment_retries": 2,
        "skip_unavailable_fragments": True,
        # Additional options for better compatibility
        "age_limit": 18,  # Try to bypass age restrictions
        "no_check_certificate": True,
        "prefer_insecure": False,
    }
    
    # Add proxy if provided
    if proxy:
        opts["proxy"] = proxy
    
    # Add FFmpeg location for Windows
    if os.name == 'nt':
        opts["ffmpeg_location"] = r"C:\ProgramData\chocolatey\bin\ffmpeg.exe"
    
    return opts

def try_cookies_from_browser(ydl_opts: Dict[str, Any]) -> Dict[str, Any]:
    """Try to add cookies from browser if available"""
    try:
        # Try to get cookies from Chrome first, then Firefox
        browsers = ['chrome', 'firefox', 'safari', 'edge']
        for browser in browsers:
            try:
                ydl_opts_with_cookies = ydl_opts.copy()
                ydl_opts_with_cookies["cookiesfrombrowser"] = (browser, None, None, None)
                return ydl_opts_with_cookies
            except:
                continue
    except:
        pass
    return ydl_opts

def extract_with_config(url: str, config: Dict[str, Any], download: bool = False, format_selector: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Extract video info using a specific YouTube client configuration"""
    try:
        ydl_opts = get_base_ydl_opts(YTDLP_PROXY)
        ydl_opts.update({
            "skip_download": not download,
            "http_headers": config.get("http_headers", {}),
            "extractor_args": config.get("extractor_args", {})
        })
        
        if download and format_selector:
            ydl_opts["format"] = format_selector
            ydl_opts["merge_output_format"] = "mp4"
        
        logger.info(f"Trying {config['name']} client for {'download' if download else 'metadata'}")
        
        # First try without cookies
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                if download:
                    return ydl.extract_info(url, download=True)
                else:
                    return ydl.extract_info(url, download=False)
            except Exception as e:
                if "sign in" in str(e).lower() or "bot" in str(e).lower():
                    # Try with cookies if bot detection occurs
                    logger.info(f"Bot detection triggered, trying {config['name']} with cookies")
                    ydl_opts_with_cookies = try_cookies_from_browser(ydl_opts)
                    with yt_dlp.YoutubeDL(ydl_opts_with_cookies) as ydl_cookies:
                        if download:
                            return ydl_cookies.extract_info(url, download=True)
                        else:
                            return ydl_cookies.extract_info(url, download=False)
                else:
                    raise e
                
    except Exception as e:
        logger.warning(f"{config['name']} client failed: {str(e)}")
        return None

async def extract_youtube_info(url: str) -> Optional[Dict[str, Any]]:
    """Extract YouTube video information using multiple strategies"""
    
    # Try each configuration sequentially with small delays (parallel was causing issues)
    for config in YOUTUBE_CONFIGS:
        try:
            result = await asyncio.get_event_loop().run_in_executor(
                None, extract_with_config, url, config, False
            )
            if result:
                logger.info(f"Successfully extracted video info using {config['name']}")
                return result
        except Exception as e:
            logger.warning(f"Extraction with {config['name']} failed: {str(e)}")
        
        # Small delay between attempts to avoid overwhelming YouTube
        await asyncio.sleep(random.uniform(0.5, 1.5))
    
    # If all configs fail, try a fallback method with generic extraction
    logger.info("All specialized configs failed, trying fallback method")
    try:
        ydl_opts = {
            "quiet": True,
            "skip_download": True,
            "http_headers": {"User-Agent": random.choice(USER_AGENTS)},
            "socket_timeout": 30,
            "retries": 1,
            "age_limit": 18,
            "no_check_certificate": True,
        }
        
        if YTDLP_PROXY:
            ydl_opts["proxy"] = YTDLP_PROXY
            
        # Try with cookies from browser as last resort
        ydl_opts = try_cookies_from_browser(ydl_opts)
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            result = ydl.extract_info(url, download=False)
            if result:
                logger.info("Fallback method succeeded")
                return result
    except Exception as e:
        logger.warning(f"Fallback method failed: {str(e)}")
    
    return None

def normalize_youtube_url(url: str) -> str:
    """Normalize various YouTube URL formats"""
    import re
    
    # Extract video ID from various URL formats
    patterns = [
        r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/|youtube\.com/v/)([a-zA-Z0-9_-]{11})',
        r'youtube\.com/watch\?.*v=([a-zA-Z0-9_-]{11})',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            video_id = match.group(1)
            return f"https://www.youtube.com/watch?v={video_id}"
    
    return url

@app.post("/api/metadata")
async def get_metadata(data: dict):
    url = data.get("url")
    if not url:
        raise HTTPException(status_code=400, detail="URL is required")
    
    # Normalize YouTube URLs
    if "youtube" in url or "youtu.be" in url:
        url = normalize_youtube_url(url)
    
    try:
        # For YouTube, use our enhanced extraction method
        if "youtube" in url or "youtu.be" in url:
            info = await extract_youtube_info(url)
            if not info:
                raise HTTPException(
                    status_code=503, 
                    detail="YouTube is currently blocking requests. This is a temporary issue that may resolve itself. Please try again later, or try using a different video URL."
                )
        else:
            # For non-YouTube URLs, use standard extraction
            ydl_opts = get_base_ydl_opts(YTDLP_PROXY)
            ydl_opts.update({
                "skip_download": True,
                "http_headers": {"User-Agent": random.choice(USER_AGENTS)}
            })
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
        
        if not info:
            raise HTTPException(status_code=400, detail="Failed to extract video information")
        
        # Prepare qualities with better filtering
        qualities = []
        seen_heights = set()
        
        for f in info.get("formats", []):
            if f.get("ext") == "mp4" and f.get("height") and f.get("vcodec") != "none":
                height = f['height']
                if height not in seen_heights and height >= 144:  # Minimum quality filter
                    qualities.append({
                        "label": f"{height}p",
                        "value": str(height),
                        "format": f['ext']
                    })
                    seen_heights.add(height)
        
        # Sort qualities by resolution (descending)
        qualities.sort(key=lambda x: int(x["value"]), reverse=True)
        
        # Ensure we have at least some qualities
        if not qualities:
            # Fallback: add any available mp4 formats
            for f in info.get("formats", []):
                if f.get("ext") == "mp4":
                    label = f"Format {f.get('format_id', 'unknown')}"
                    if f.get("height"):
                        label = f"{f['height']}p"
                    elif f.get("format_note"):
                        label = f.get("format_note")
                    
                    qualities.append({
                        "label": label,
                        "value": f.get('format_id', 'unknown'),
                        "format": f['ext']
                    })
                    if len(qualities) >= 5:  # Limit fallback options
                        break
        
        # Platform detection with better coverage
        webpage_url = info.get("webpage_url", url).lower()
        if "youtube" in webpage_url or "youtu.be" in webpage_url:
            platform = "youtube"
        elif "twitter" in webpage_url or "x.com" in webpage_url:
            platform = "twitter"
        elif "instagram" in webpage_url:
            platform = "instagram"
        elif "tiktok" in webpage_url:
            platform = "tiktok"
        elif "facebook" in webpage_url or "fb.watch" in webpage_url:
            platform = "facebook"
        else:
            platform = "unknown"
        
        return {
            "title": info.get("title", "Unknown Title"),
            "thumbnail": info.get("thumbnail"),
            "duration": str(info.get("duration", 0)) + "s" if info.get("duration") else "Unknown",
            "platform": platform,
            "qualities": qualities
        }
        
    except HTTPException:
        raise
    except Exception as e:
        error_msg = str(e).lower()
        if "sign in to confirm" in error_msg or "bot" in error_msg:
            raise HTTPException(
                status_code=503, 
                detail="YouTube is temporarily blocking automated requests. This is a common issue that resolves itself. Please try again in a few minutes, or try a different video."
            )
        elif "429" in error_msg or "too many requests" in error_msg:
            raise HTTPException(
                status_code=429, 
                detail="Rate limit exceeded. Please wait a moment before trying again."
            )
        elif "proxy" in error_msg:
            raise HTTPException(
                status_code=502, 
                detail="Network connectivity issue. Please try again later."
            )
        else:
            logger.error(f"Metadata extraction error: {str(e)}")
            raise HTTPException(
                status_code=400, 
                detail="Unable to process this video. Please check the URL and try again."
            )

async def download_with_config(url: str, quality: str, filename: str, config: Dict[str, Any]) -> bool:
    """Download video using a specific configuration"""
    try:
        format_selector = f"bestvideo[height={quality}]+bestaudio/best[height={quality}]"
        ydl_opts = get_base_ydl_opts(YTDLP_PROXY)
        ydl_opts.update({
            "format": format_selector,
            "outtmpl": filename,
            "merge_output_format": "mp4",
            "http_headers": config.get("http_headers", {}),
            "extractor_args": config.get("extractor_args", {})
        })
        
        logger.info(f"Attempting download with {config['name']} client")
        
        # First try without cookies
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            return os.path.exists(filename)
        except Exception as e:
            if "sign in" in str(e).lower() or "bot" in str(e).lower():
                # Try with cookies if bot detection occurs
                logger.info(f"Download bot detection triggered, trying {config['name']} with cookies")
                ydl_opts_with_cookies = try_cookies_from_browser(ydl_opts)
                with yt_dlp.YoutubeDL(ydl_opts_with_cookies) as ydl_cookies:
                    ydl_cookies.download([url])
                return os.path.exists(filename)
            else:
                raise e
        
    except Exception as e:
        logger.warning(f"Download with {config['name']} failed: {str(e)}")
        return False

@app.post("/api/download")
async def download_video(data: dict):
    url = data.get("url")
    quality = data.get("quality")
    if not url or not quality:
        raise HTTPException(status_code=400, detail="URL and quality are required")
    
    # Normalize YouTube URLs
    if "youtube" in url or "youtu.be" in url:
        url = normalize_youtube_url(url)
    
    # Use a unique temporary filename
    filename = f"download_{os.getpid()}_{int(time.time())}_{quality}.mp4"
    
    try:
        success = False
        
        if "youtube" in url or "youtu.be" in url:
            # For YouTube, try multiple client configurations sequentially
            for config in YOUTUBE_CONFIGS:
                try:
                    result = await asyncio.get_event_loop().run_in_executor(
                        None, download_with_config, url, quality, filename, config
                    )
                    if result:
                        success = True
                        logger.info(f"Download successful with {config['name']}")
                        break
                except Exception as e:
                    logger.warning(f"Download attempt with {config['name']} failed: {str(e)}")
                
                # Small delay between attempts to avoid overwhelming YouTube
                await asyncio.sleep(random.uniform(0.5, 1.5))
        else:
            # For non-YouTube URLs, use standard method
            ydl_opts = get_base_ydl_opts(YTDLP_PROXY)
            ydl_opts.update({
                "format": f"bestvideo[height={quality}]+bestaudio/best[height={quality}]",
                "outtmpl": filename,
                "merge_output_format": "mp4",
                "http_headers": {"User-Agent": random.choice(USER_AGENTS)}
            })
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            success = os.path.exists(filename)
        
        if not success:
            raise Exception("All download methods failed")
        
        def iterfile():
            try:
                with open(filename, "rb") as f:
                    yield from f
            finally:
                if os.path.exists(filename):
                    os.remove(filename)
        
        return StreamingResponse(
            iterfile(), 
            media_type="video/mp4", 
            headers={
                "Content-Disposition": f'attachment; filename="video_{quality}p.mp4"'
            }
        )
        
    except Exception as e:
        # Clean up file if it exists
        if os.path.exists(filename):
            os.remove(filename)
        
        error_msg = str(e).lower()
        if "sign in to confirm" in error_msg or "bot" in error_msg:
            raise HTTPException(
                status_code=503, 
                detail="YouTube is temporarily blocking downloads. This is a temporary restriction. Please try again later."
            )
        elif "429" in error_msg or "too many requests" in error_msg:
            raise HTTPException(
                status_code=429, 
                detail="Rate limit exceeded. Please wait before downloading again."
            )
        elif "proxy" in error_msg:
            raise HTTPException(
                status_code=502, 
                detail="Network connectivity issue. Please try again later."
            )
        else:
            logger.error(f"Download error: {str(e)}")
            raise HTTPException(
                status_code=500, 
                detail="Download failed. Please try again with a different quality or check if the video is available."
            )
