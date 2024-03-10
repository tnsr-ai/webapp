"use client";
import * as React from "react";
import Modal from "@mui/material/Modal";
import { XMarkIcon } from "@heroicons/react/20/solid";
import { VideoFilter } from "./FilterComponents/VideoFilter";
import { ImageFilter } from "./FilterComponents/ImageFilter";
import { AudioFilter } from "./FilterComponents/AudioFilter";
import { usePathname } from "next/navigation";


export default function FilterModal(props: any) {
  const setStatus = (e: any) => {
    if (e.target.id === "wrapper") {
      props.setFilterShow(false);
    }
  };
  const onclose = () => {
    props.setFilterShow(false);
  };
  const filterProps = {
    "content_data": props.content_data,
    "model_config": props.model_config,
    "model_tier": props.tier_config,
    "user_tier": props.user_tier,
  };
  const pathname = usePathname().replace("/", "").split("/")[0];
  const firstLetter = pathname.charAt(0).toUpperCase();
  const restLetter = pathname.slice(1);
  const contentNameCapitalized = firstLetter + restLetter;
  let AIFilters;
  if (contentNameCapitalized === "Video") {
    AIFilters = (
      <VideoFilter
        id={props.id}
        content_data={props.content_data}
        setFilterShow={props.setFilterShow}
        filterConfig={filterProps}
      />
    );
  } else if (contentNameCapitalized === "Image") {
    AIFilters = (
      <ImageFilter
        id={props.id}
        content_data={props.content_data}
        setFilterShow={props.setFilterShow}
        filterConfig={filterProps}
      />
    );
  } else {
    AIFilters = (
      <AudioFilter
        id={props.id}
        content_data={props.content_data}
        setFilterShow={props.setFilterShow}
        filterConfig={filterProps}
      />
    );
  }

  return (
    <div>
      <Modal
        open={props.filterShow}
        onClose={() => {
          props.setFilterShow(false);
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
              <div className="flex flex-col">
                <button className="place-self-end" onClick={() => onclose()}>
                  <XMarkIcon className="w-8 fill-white cursor-pointer" />
                </button>
                <div className="bg-white p-2 rounded-xl">
                  <div id="title">
                    <span className="text-2xl font-semibold m-3">{`${contentNameCapitalized} AI Filters`}</span>
                    <div className="">{AIFilters}</div>
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
