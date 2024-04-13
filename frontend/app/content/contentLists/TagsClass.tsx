interface Dictionary<T> {
  [Key: string]: T;
}

export const tagColor: Dictionary<string> = {
  Original:
    "inline-flex items-center bg-gray-500 p-1 text-xs font-medium text-white rounded-md ring-1 ring-gray-500/10",
  "Super Resolution":
    "inline-flex items-center rounded-md bg-yellow-400 p-1 text-xs font-medium text-black ring-1 ring-inset ring-yellow-500/10",
  "Video Deblurring":
    "inline-flex items-center bg-red-400 p-1 text-xs font-medium text-black rounded-md ring-1 ring-gray-500/10",
  "Video Denoising":
    "inline-flex items-center bg-fuchsia-400 p-1 text-xs font-medium text-black rounded-md ring-1 ring-gray-500/10",
  "Face Restoration":
    "inline-flex items-center bg-lime-400 p-1 text-xs font-medium text-black rounded-md ring-1 ring-gray-500/10",
  "B/W To Color":
    "inline-flex items-center bg-teal-400 p-1 text-xs font-medium text-black rounded-md ring-1 ring-gray-500/10",
  "Slow Motion":
    "inline-flex items-center bg-indigo-400 p-1 text-xs font-medium text-black rounded-md ring-1 ring-gray-500/10",
  "Video Interpolation":
    "inline-flex items-center bg-violet-400 p-1 text-xs font-medium text-black rounded-md ring-1 ring-gray-500/10",
  "Video Deinterlacing":
    "inline-flex items-center bg-rose-400 p-1 text-xs font-medium text-black rounded-md ring-1 ring-gray-500/10",
  "Image Deblurring":
    "inline-flex items-center bg-red-400 p-1 text-xs font-medium text-black rounded-md ring-1 ring-gray-500/10",
  "Image Denoising":
    "inline-flex items-center bg-fuchsia-400 p-1 text-xs font-medium text-black rounded-md ring-1 ring-gray-500/10",
  "Image Inpainting":
    "inline-flex items-center bg-green-400 p-1 text-xs font-medium text-black rounded-md ring-1 ring-gray-500/10",
  "Audio Separation":
    "inline-flex items-center rounded-md bg-red-400 p-1 text-xs font-medium text-black ring-1 ring-inset ring-yellow-500/10",
  "Speech Enhancement":
    "inline-flex items-center rounded-md bg-blue-400 p-1 text-xs font-medium text-black ring-1 ring-inset ring-yellow-500/10",
  Transcription:
    "inline-flex items-center rounded-md bg-pink-400 p-1 text-xs font-medium text-black ring-1 ring-inset ring-yellow-500/10",
  "Remove Background":
    "inline-flex items-center rounded-md bg-blue-400 p-1 text-xs font-medium text-black ring-1 ring-inset ring-yellow-500/10",
  Processing: "yellow",
  Completed: "green",
  Failed: "red",
  Cancelled: "red",
};
