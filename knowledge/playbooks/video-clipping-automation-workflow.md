# Video Clipping & Automated Posting Workflow

**Pipeline**: Google Drive/Photos → AI Clipping Tool → Repurpose.io → Multi-Platform Distribution

---

## Architecture Overview

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Google Drive/  │────▶│   AI Clipping   │────▶│   Repurpose.io  │────▶│  Social Platforms│
│  Google Photos  │     │   (OpusClip)    │     │   (Distribution) │     │  TikTok, IG, YT  │
└─────────────────┘     └─────────────────┘     └─────────────────┘     └─────────────────┘
     SOURCE              CLIPPING + EDIT          SCHEDULING           DESTINATIONS
```

**Why this architecture:**
- Google Drive = unlimited storage, accessible anywhere
- AI Clipping = handles viral moment detection, captions, formatting
- Repurpose.io = scheduled multi-platform posting without manual uploads

---

## Step 1: Choose Your AI Clipping Tool

### Recommended: OpusClip

| Feature | OpusClip |
|---------|----------|
| **Google Drive Import** | Yes (Pro plan) |
| **Auto-Clipping AI** | ClipAnything - works on all video types |
| **Captions** | Auto-generated with 97%+ accuracy |
| **Virality Score** | AI scores each clip's viral potential |
| **Built-in Scheduler** | Yes, multi-platform |
| **Pricing** | Free: 60 min/mo, Pro: $15/mo for 150 min |

**Setup:**
1. Create account at [opus.pro](https://www.opus.pro/)
2. Connect Google Drive under Sources
3. Upload long-form video or point to Drive folder
4. AI generates 10-20 clips per video
5. Review clips, select best performers by virality score
6. Export to Drive folder for Repurpose.io pickup

### Alternatives

| Tool | Best For | Pricing | Google Drive |
|------|----------|---------|--------------|
| **Vizard AI** | More control/precision editing | $14.50/mo (600 min) | Yes |
| **quso.ai** | All-in-one (clip + schedule) | Free tier available | Yes |
| **Spikes Studio** | Gaming/streaming content | Free 30 min/mo | Limited |

---

## Step 2: Set Up Google Drive Folder Structure

Create this folder structure in Google Drive:

```
📁 Video_Pipeline/
├── 📁 01_Raw_Footage/          ← Upload long-form videos here
├── 📁 02_Clips_Ready/          ← OpusClip exports here
│   ├── 📁 TikTok_Ready/        ← 9:16 vertical clips
│   ├── 📁 Shorts_Ready/        ← YT Shorts (same as TikTok)
│   └── 📁 Reels_Ready/         ← IG Reels (same or slight variations)
├── 📁 03_Posted/               ← Move here after posting (archive)
└── 📁 Descriptions/            ← TXT files with captions (optional)
```

**Caption Files (Optional):**
Repurpose.io can pull descriptions from TXT files. Create a file with the SAME NAME as your video:

```
video_clip_001.mp4
video_clip_001.txt  ← Contains caption/hashtags
```

---

## Step 3: Connect Repurpose.io to Google Drive

### Initial Setup

1. Go to [repurpose.io](https://repurpose.io) → Create account
2. Navigate to **Connections** (left menu)
3. Click **Add a New Connection** → Select **Google Drive**
4. Authorize access to your Google account
5. Name the connection (e.g., "Video Pipeline Drive")

### Create Workflow: Google Drive → TikTok

1. Go to **Workflows** → **Create New Workflow**
2. **Source:** Google Drive
3. **Select Folder:** `Video_Pipeline/02_Clips_Ready/TikTok_Ready/`
4. **Destination:** TikTok
5. **Settings:**
   - Video format: Full video (default)
   - Enable "Remove watermark" if available
6. **Publishing Mode:** Set to **Auto**

### Create Additional Workflows

Repeat for each destination:
- Google Drive (`Shorts_Ready/`) → YouTube Shorts
- Google Drive (`Reels_Ready/`) → Instagram Reels
- Google Drive → Facebook Reels
- Google Drive → LinkedIn (if applicable)

---

## Step 4: Configure Auto-Publishing Schedule

### In Repurpose.io

1. Go to each workflow → **Settings**
2. Enable **Auto Publish Schedule**
3. Set posting times:

| Platform | Best Times | Frequency |
|----------|------------|-----------|
| TikTok | 6-9am, 12-3pm, 7-9pm | 1-3x/day |
| IG Reels | 11am-1pm, 7-9pm | 1-2x/day |
| YT Shorts | 12-3pm, 6-9pm | 1-2x/day |

**Rules:**
- Minimum 2-hour gap between posts
- Up to 5 time slots per day
- Stagger platforms to avoid simultaneous posting

---

## Step 5: Complete Automation Workflow

### Daily Workflow (5-10 min)

```
1. Upload raw footage to 📁 01_Raw_Footage/
2. Open OpusClip → Import from Drive
3. Let AI generate clips (2-5 min)
4. Review clips by virality score
5. Export selected clips to 📁 02_Clips_Ready/{platform}/
6. Repurpose.io automatically picks up and posts on schedule
```

### Weekly Batch Workflow (30-60 min)

```
1. Record/collect all raw footage for the week
2. Batch upload to 📁 01_Raw_Footage/
3. Process all videos through OpusClip in one session
4. Organize clips into platform folders
5. Let Repurpose.io distribute throughout the week
```

---

## Step 6: Advanced Automation (Optional)

### Option A: OpusClip Direct Posting

Skip Repurpose.io for simpler workflow:
1. OpusClip has built-in scheduler
2. Connect social accounts directly in OpusClip
3. Schedule clips immediately after AI generates them

**Pros:** Fewer tools, simpler
**Cons:** Less scheduling flexibility than Repurpose.io

### Option B: quso.ai All-in-One

Replace both OpusClip + Repurpose.io:
1. quso.ai clips videos AND schedules posts
2. Single platform for entire workflow
3. Built-in social media management

### Option C: n8n Custom Automation

For technical users wanting full control:
1. Set up n8n workflow
2. Watch Google Drive folder for new files
3. Auto-trigger posting via APIs
4. Full customization possible

---

## Tool Comparison Matrix

| Need | Best Tool | Why |
|------|-----------|-----|
| **Easiest setup** | quso.ai | All-in-one, fewer integrations |
| **Best clip quality** | OpusClip | Superior AI, virality scoring |
| **Most scheduling control** | Repurpose.io | Advanced scheduling, multiple destinations |
| **Lowest cost** | Vizard + Repurpose | Vizard: 600 min for $14.50 |
| **Gaming/streaming** | Spikes Studio | Optimized for that content type |

---

## Recommended Stack

### For Your Use Case (Scripts → Clips → Multi-platform)

```
Google Photos/Drive
       ↓
   OpusClip Pro ($15/mo)
   - Import from Drive
   - AI clips with captions
   - Virality scoring
       ↓
   Export to Drive folder
       ↓
   Repurpose.io ($20/mo)
   - Auto-pickup from Drive
   - Multi-platform scheduling
   - Watermark removal
       ↓
   TikTok + IG Reels + YT Shorts + Facebook
```

**Total cost:** ~$35/mo for fully automated pipeline

### Budget Alternative

```
Google Photos/Drive
       ↓
   quso.ai (Free tier or $19/mo)
   - Clips + schedules in one tool
   - Direct platform connections
       ↓
   All platforms
```

**Total cost:** $0-19/mo

---

## Troubleshooting

### Repurpose.io Not Picking Up Files

1. Check folder path in workflow matches exactly
2. Verify Google Drive connection is active
3. Confirm workflow is set to "Auto" not "Manual"
4. Check file format is supported (.mp4, .mov)

### Clips Not Getting Views

1. Review virality scores in OpusClip (aim for 70+)
2. Check hook in first 3 seconds
3. Verify captions are readable
4. Test different posting times

### Google Drive Sync Issues

1. Use Google Drive desktop app for faster sync
2. Or use Google Photos → automatically syncs to Drive
3. Ensure sufficient Drive storage

---

## Sources

- [OpusClip](https://www.opus.pro/) - AI video clipping
- [Repurpose.io](https://repurpose.io/) - Multi-platform distribution
- [Repurpose.io Google Drive Setup](https://support.repurpose.io/en/article/connecting-your-google-drive-1ymmdi5/)
- [Vizard AI](https://vizard.ai/) - Alternative clipper
- [quso.ai](https://quso.ai/) - All-in-one solution
- [Spikes Studio](https://www.spikes.studio/) - Gaming/streaming focus
