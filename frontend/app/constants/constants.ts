export const dashboardStats = [
  {
    id: 1,
    name: "Video",
    icon: "/icons/video_stats.png",
    key: "video_processed",
  },
  {
    id: 2,
    name: "Image",
    icon: "/icons/image_stats.png",
    key: "image_processed",
  },
  {
    id: 3,
    name: "Audio",
    icon: "/icons/audio_stats.png",
    key: "audio_processed",
  },
];

export const networkStats = [
  {
    id: 1,
    name: "Download",
    icon: "/icons/download.png",
    key: "downloads",
  },
  {
    id: 2,
    name: "Upload",
    icon: "/icons/upload.png",
    key: "uploads",
  },
  {
    id: 3,
    name: "Storage",
    icon: "/icons/storage.png",
    key: "storage",
  },
  {
    id: 4,
    name: "GPU Usage",
    icon: "/icons/gpu.png",
    key: "gpu_usage",
  },
];

export const userPlans = [
  {
    name: "Free",
    times: 0,
    features: [
      "Storage upto 2GB",
      "1 filters per video",
      "Process one job at a time",
      "Files deleted after 1 week",
      "Max duration on video 3 minutes",
    ],
  },
  {
    name: "Standard",
    times: 30,
    features: [
      "Storage upto 20GB",
      "5 filters per video",
      "Process upto 5 jobs at a time",
      "Files deleted after 1 month",
      "No limit on duration of video",
    ],
  },
  {
    name: "Deluxe",
    times: 100,
    features: [
      "Storage upto 100GB",
      "8 filters per video",
      "Process upto 10 videos at a time",
      "Files deleted after 3 month",
      "No limit on duration of video",
    ],
  },
];

export const videoData = {
  acceptedFiles: {
    "video/mp4": [".mp4"],
    "video/m4a": [".m4a"],
    "video/quicktime": [".mov"],
    "video/x-matroska": [".mkv"],
    "video/webm": [".webm"],
    "video/wmv": [".wmv"],
  },
  maxFileSizeInBytes: 5000000000,
  dropzoneMsg: "MP4, MOV, MKV or WEBM (MAX. 5GB)",
};

export const imageData = {
  acceptedFiles: {
    "image/png": [".png"],
    "image/jpeg": [".jpeg"],
    "image/jpg": [".jpg"],
    "image/webp": [".webp"],
  },
  maxFileSizeInBytes: 50000000,
  dropzoneMsg: "PNG, JPEG, JPG or WEBP (MAX. 50MB)",
};

export const audioData = {
  acceptedFiles: {
    "audio/mp3": [".mp3"],
    "audio/wav": [".wav"],
    "audio/mpeg": [".mp3"],
    "audio/aac": [".aac"],
  },
  maxFileSizeInBytes: 200000000,
  dropzoneMsg: "MP3, WAV or AAC (MAX. 200MB)",
};

export const fileSizeUnits = [
  "bytes",
  "KB",
  "MB",
  "GB",
  "TB",
  "PB",
  "EB",
  "ZB",
  "YB",
];
