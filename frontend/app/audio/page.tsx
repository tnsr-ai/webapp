"use client";
import AppBar from "../components/AppBar";
import SideDrawer from "../components/SideDrawer";
import DropZone from "../components/DropZone";
import { useState } from "react";
import ContentList from "../content/contentCards/ContentList";
import { audioData } from "../constants/constants";

export default function Audio() {
  const [AudioUpload, setAudioUpload] = useState(false);

  return (
    <div className="grid grid-cols-1 lg:grid-cols-[296px_1fr] grid-rows-[minmax(62px,_90px)_1fr]">
      <div className="lg:col-start-1 lg:col-end-2 lg:row-start-1 lg:row-span-2 hidden lg:block">
        <div className="fixed top-0 h-full">
          <SideDrawer />
        </div>
      </div>
      <div className="sticky top-0">
        <AppBar />
      </div>
      <div className="mt-5">
        <div>
          <DropZone
            filetype={audioData.dropzoneMsg}
            acceptedtype={audioData.acceptedFiles}
            setVideoUpload={setAudioUpload}
            maxFileSize={audioData.maxFileSizeInBytes}
          />
        </div>
        <div className="flex-col max-w-[1500px] flex m-auto mt-5 mb-10">
          <div>
            <ContentList
              VideoUpload={AudioUpload}
              setVideoUpload={setAudioUpload}
            />
          </div>
        </div>
      </div>
    </div>
  );
}
