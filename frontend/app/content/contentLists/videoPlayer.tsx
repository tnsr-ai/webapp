"use client";
import * as React from "react";
import Modal from "@mui/material/Modal";
import { XMarkIcon } from "@heroicons/react/20/solid";
import { Media, Video, Audio } from "@vidstack/player-react";

export default function VideoPlayer(props: any) {
  const setStatus = (e: any) => {
    if (e.target.id === "wrapper") {
      props.setVideoPlayer(false);
    }
  };
  const onclose = () => {
    props.setVideoPlayer(false);
  };
  return (
    <div>
      <Modal
        open={props.videoPlayer}
        onClose={() => {
          props.setVideoPlayer(false);
        }}
        aria-labelledby="modal-modal-title"
        aria-describedby="modal-modal-description"
      >
        <div className="h-full w-full flex justify-center items-center">
          <div className="fixed">
            <div
              className="fixed inset-0 bg-gray-900 bg-opacity-10 backdrop-blur-[2px] flex justify-center items-center"
              id="wrapper"
              onClick={setStatus}
            >
              <div className="flex-col mt-5">
                <div className="w-[100%] flex justify-end items-end">
                  <XMarkIcon
                    className="w-8 fill-white cursor-pointer"
                    onClick={() => {
                      onclose();
                    }}
                  />
                </div>
                <div className="rounded-lg m-2 p-2 backdrop-blur-sm bg-white/30 flex justify-center items-center">
                  <div className="flex justify-center items-center">
                    <Media>
                      {props.type === "video" && (
                        <Video
                          loading="visible"
                          controls
                          preload="auto"
                          key={props.link}
                        >
                          <video
                            src={props.link}
                            preload="true"
                            data-video="0"
                            controls
                            controlsList="nodownload"
                            key={props.link}
                            className="max-w-[80vh] max-h-[80vh] min-w-[250px] min-h-[250px]"
                          />
                        </Video>
                      )}
                      {props.type === "audio" && (
                        <Audio
                          loading="visible"
                          controls
                          preload="auto"
                          key={props.link}
                        >
                          <audio
                            src={props.link}
                            preload="true"
                            data-video="0"
                            controls
                            controlsList="nodownload"
                            key={props.link}
                          />
                        </Audio>
                      )}
                    </Media>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </Modal>
    </div>
  );
}
