import os
import re
import numpy as np
import cv2
from PIL import Image
import atexit

# --- MOVIEPY v2.2.1 IMPORTS ---
from moviepy.audio.io.AudioFileClip import AudioFileClip
from moviepy.audio.AudioClip import CompositeAudioClip
from moviepy.audio.fx.MultiplyVolume import MultiplyVolume
from moviepy.audio.fx.AudioLoop import AudioLoop
from moviepy.video.VideoClip import VideoClip, ImageClip
from moviepy.video.compositing.CompositeVideoClip import concatenate_videoclips
from moviepy.video.io.VideoFileClip import VideoFileClip
from moviepy.video.fx.Loop import Loop
from media.music_provider import MusicProvider
from PIL import Image, ImageFilter, ImageEnhance
# ------------------------------

from core.schemas import FullScript

class VideoEditor:
    def __init__(self, output_dir="output/video"):
        self.output_dir = output_dir
        self.assets_dir = "output/assets"
        self.audio_dir = "output/audio"
        os.makedirs(output_dir, exist_ok=True)
        
        self.w = 1920
        self.h = 1080
        self.fps = 24

    def _sanitize_filename(self, text: str) -> str:
        clean = re.sub(r'[<>:"/\\|?*]', '', text)
        return clean.replace(' ', '_')

    def _preprocess_image(self, image_path):
        cache_path = image_path + ".cache.npy"
        
        # 1. HIT CACHE
        if os.path.exists(cache_path):
            try:
                return np.load(cache_path)
            except Exception: pass

        # 2. MISS CACHE - PROCESS
        with Image.open(image_path) as img:
            img = img.convert("RGB")
            img_w, img_h = img.size
            img_ratio = img_w / img_h
            target_ratio = self.w / self.h # 1.77
            
            # --- DECISION LOGIC ---
            # If image is Portrait (Vertical) or Square-ish (< 1.4 ratio), use Blurred Pillars
            if img_ratio < 1.4:
                # A. CREATE BACKGROUND (Blurred & Darkened)
                # Resize to fill width, then crop height
                bg_scale = self.w / img_w
                bg_w = self.w
                bg_h = int(img_h * bg_scale)
                bg = img.resize((bg_w, bg_h), Image.Resampling.LANCZOS)
                
                # Center Crop Vertical
                top = (bg_h - self.h) // 2
                if top < 0: top = 0
                bg = bg.crop((0, top, self.w, top + self.h))
                
                # Blur & Darken
                bg = bg.filter(ImageFilter.GaussianBlur(radius=30))
                bg = ImageEnhance.Brightness(bg).enhance(0.6)
                
                # B. CREATE FOREGROUND (Fit Height)
                # Resize to fit height (1080), maintain ratio
                fg_scale = self.h / img_h
                fg_h = self.h
                fg_w = int(img_w * fg_scale)
                fg = img.resize((fg_w, fg_h), Image.Resampling.LANCZOS)
                
                # C. COMPOSITE
                # Paste FG onto BG center
                final_img = bg.copy()
                x_pos = (self.w - fg_w) // 2
                final_img.paste(fg, (x_pos, 0))
                
                img_array = np.array(final_img)

            # --- LANDSCAPE LOGIC (Existing Crop) ---
            else:
                if img_ratio > target_ratio:
                    # Too Wide -> Fit Height, Crop Width
                    new_h = self.h
                    new_w = int(img_w * (self.h / img_h))
                    img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
                    left = (new_w - self.w) // 2
                    img = img.crop((left, 0, left + self.w, self.h))
                else:
                    # Too Tall (but still landscape) -> Fit Width, Crop Height
                    new_w = self.w
                    new_h = int(img_h * (self.w / img_w))
                    img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
                    top = (new_h - self.h) // 2
                    img = img.crop((0, top, self.w, top + self.h))
                
                img_array = np.array(img)

        # 3. SAVE CACHE
        np.save(cache_path, img_array)
        return img_array

    def _create_zooming_clip(self, image_path, duration):
        # Load Base Image (Cached)
        base_img = self._preprocess_image(image_path)
        h, w = base_img.shape[:2]

        def make_frame(t):
            # 1. Calculate Scale (Linear interpolation)
            # t goes from 0 to duration
            scale = 1.0 + 0.04 * (t / duration)
            
            # 2. OpenCV Resize (C++ Speed)
            # Only resize to the new needed dimension
            new_w = int(w * scale)
            new_h = int(h * scale)
            
            # cv2.INTER_LINEAR is roughly equivalent to PIL BILINEAR but faster
            resized = cv2.resize(base_img, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
            
            # 3. Center Crop (NumPy Slicing is instant)
            center_x = new_w // 2
            center_y = new_h // 2
            
            x1 = center_x - (self.w // 2)
            y1 = center_y - (self.h // 2)
            
            # Safety checks for rounding errors
            if x1 < 0: x1 = 0
            if y1 < 0: y1 = 0
            
            # Return the cropped 1920x1080 frame
            return resized[y1:y1+self.h, x1:x1+self.w]

        # Returns a clip that generates its own frames when asked
        clip = VideoClip(make_frame, duration=duration)
        clip.fps = self.fps
        return clip


    def assemble_video(self, script: FullScript, bg_music_path: str = None):
        print(f"🎞️  Assembling video for: {script.title}")
        
        final_clips = []
        
        # --- VISUAL ASSEMBLY ---
        for segment in script.segments:
            seg_idx = segment.segment_order
            print(f"   Processing Segment {seg_idx}...")
            
            # Audio
            audio_path = os.path.join(self.audio_dir, f"segment_{seg_idx:02d}.mp3")
            if not os.path.exists(audio_path): continue
            
            # Lazy load audio duration
            audio_clip = AudioFileClip(audio_path)
            duration = audio_clip.duration
            
            # Assets (Now scans for .mp4 AND images)
            seg_assets_dir = os.path.join(self.assets_dir, f"segment_{seg_idx:02d}")
            if os.path.exists(seg_assets_dir):
                # Sort ensures shot_00, shot_01 play in order regardless of file type
                asset_files = sorted([
                    f for f in os.listdir(seg_assets_dir) 
                    if f.endswith(('.jpg', '.png', '.jpeg', '.mp4'))
                ])
            else:
                asset_files = []
            
            if not asset_files:
                # Fallback Black Screen
                black = np.zeros((self.h, self.w, 3), dtype=np.uint8)
                final_clips.append(ImageClip(black).with_duration(duration).with_audio(audio_clip))
                continue

            # Create Clips
            duration_per_asset = duration / len(asset_files)
            segment_visuals = []
            
            for asset_file in asset_files:
                asset_path = os.path.join(seg_assets_dir, asset_file)
                
                if asset_file.endswith(".mp4"):
                    # --- VIDEO HANDLER (Stock Footage) ---
                    clip = VideoFileClip(asset_path)
                    
                    # 1. Resize to Fill 1920x1080 (Cover Logic)
                    if (clip.w / clip.h) > (self.w / self.h):
                        clip = clip.resized(height=self.h) # Too wide -> fit height
                    else:
                        clip = clip.resized(width=self.w)  # Too tall -> fit width
                        
                    # 2. Center Crop to exact 1920x1080
                    clip = clip.cropped(
                        x_center=clip.w/2, 
                        y_center=clip.h/2, 
                        width=self.w, 
                        height=self.h
                    )
                    
                    # 3. Handle Duration (Loop if short, Trim if long)
                    if clip.duration < duration_per_asset:
                        clip = clip.with_effects([Loop(duration=duration_per_asset)])
                    else:
                        clip = clip.subclipped(0, duration_per_asset)
                        
                else:
                    # --- IMAGE HANDLER (OpenCV Zoom) ---
                    clip = self._create_zooming_clip(asset_path, duration_per_asset)
                
                segment_visuals.append(clip)
            
            # CHAIN method (Fastest)
            segment_video = concatenate_videoclips(segment_visuals, method="chain")
            segment_video = segment_video.with_audio(audio_clip)
            final_clips.append(segment_video)

        if not final_clips: return

        print("   Concatenating segments...")
        final_video = concatenate_videoclips(final_clips, method="chain")
        
        # --- AUDIO MIXING ---
        music_clip = None
        if bg_music_path and os.path.exists(bg_music_path):
            print(f"   🎵 Adding Background Music...")
            music_clip = AudioFileClip(bg_music_path)
            
            if music_clip.duration < final_video.duration:
                music_clip = music_clip.with_effects([AudioLoop(duration=final_video.duration)])
            else:
                music_clip = music_clip.subclipped(0, final_video.duration)
            
            music_clip = music_clip.with_effects([MultiplyVolume(0.07)]) # ***Volume adjustment***
            final_audio = CompositeAudioClip([final_video.audio, music_clip])
            final_video = final_video.with_audio(final_audio)

        # --- RENDERING (TURBO + LOW RAM) ---
        safe_title = self._sanitize_filename(script.title)
        output_path = os.path.join(self.output_dir, f"final_video_{safe_title}.mp4")
        
        print("   🚀 Rendering with OpenCV Streaming + NVENC...")
        
        try:
            final_video.write_videofile(
                output_path, 
                fps=self.fps, 
                codec="h264_nvenc",
                audio_codec="aac",
                threads=8,  # Ryzen 5600 
                ffmpeg_params=[
                    "-preset", "p1",      # Speed
                    "-rc", "vbr",         # Variable Bitrate
                    "-cq", "23",          # Quality
                    "-b:v", "0",          # Auto bitrate
                    "-pix_fmt", "yuv420p"
                ]
            )
        except Exception as e:
            print(f"   ⚠️ GPU Error ({e}). Fallback to CPU.")
            final_video.write_videofile(output_path, fps=24, codec="libx264", threads=12)
        finally:
            # Explicit cleanup of moviepy resources
            try:
                if final_video and hasattr(final_video, 'close'):
                    final_video.close()
                if music_clip and hasattr(music_clip, 'close'):
                    music_clip.close()
                # Clean up all segment clips
                for clip in final_clips:
                    if hasattr(clip, 'close'):
                        clip.close()
                    if hasattr(clip, 'audio') and clip.audio and hasattr(clip.audio, 'close'):
                        clip.audio.close()
            except Exception:
                pass  # Ignore cleanup errors
        
        print(f"\n✅ Video Render Complete: {output_path}")

def run_video_assembly(script: FullScript):
    editor = VideoEditor()
    music_provider = MusicProvider()

    title_lower = script.title.lower()
    if any(x in title_lower for x in ["war", "crisis", "attack", "danger", "scandal"]):
        mood = "suspense"
    elif any(x in title_lower for x in ["future", "ai", "tech", "cyber", "space"]):
        mood = "futuristic"
    elif any(x in title_lower for x in ["money", "market", "economy", "finance"]):
        mood = "corporate"
    else:
        mood = "documentary" # Default safe category
        
    # 2. Fetch the Dynamic Track
    print(f"🎵 Auto-DJ: Selected mood '{mood}' for '{script.title}'")
    bg_music_path = music_provider.fetch_music(mood)
    
    # 3. Assemble
    editor.assemble_video(script, bg_music_path=bg_music_path)