"use client";
import Link from "next/link";
import React from "react";
import Image from "next/image";
import { Tooltip } from "@mantine/core";
import DropDown from "./DropDown";
import { usePathname } from "next/navigation";
import { useState, useEffect } from "react";

export default function ContentCard(props: any) {
  let title;
  const [isLoaded, setIsLoaded] = React.useState(false);
  const [shouldPulse, setShouldPulse] = React.useState(false);
  title = props.data["title"];
  let title_len = title.length;
  if (title_len > 20) {
    title = title.substring(0, 20) + "...";
  }
  let file_ext = props.data["title"].split(".");
  file_ext = file_ext[file_ext.length - 1].toUpperCase();
  let content_info;
  let content_info_css;
  content_info_css = "text-gray-600";
  const pathname = usePathname().replace("/", "");
  if (props.type === "video") {
    let fps_data = parseFloat(props.data["fps"]).toFixed(2);
    if (Number(fps_data) > 0) {
      content_info = `${file_ext} - ${props.data["size"]} - ${props.data["duration"]} - ${fps_data} FPS`;
    } else {
      content_info = `${file_ext} - ${props.data["size"]}`;
    }
  }
  if (props.type === "audio") {
    content_info = `${file_ext} - ${props.data["size"]} - ${props.data["duration"]} - ${props.data["hz"]} HZ`;
  }
  if (props.type === "image") {
    content_info = `${file_ext} - ${props.data["size"]} - ${props.data["resolution"]}`;
  }
  if (props.data["status"] === "indexing") {
    content_info = "Indexing in progress";
  }
  if (props.data["status"] === "cancelled") {
    content_info = "Failed - " + props.data["md5"];
    content_info_css = "text-red-600 font-semibold";
  }

  React.useEffect(() => {
    if (props.data["status"] === "indexing") {
      setShouldPulse(true);
    } else {
      setShouldPulse(false);
    }
  }, [props.data["status"]]);

  return (
    <div key={props.data["title"]} className="w-full">
      <div className="w-full h-[312px]">
        {props.data["status"] != "completed" && (
          <div
            className={`h-full w-full ${shouldPulse ? "animate-pulse" : ""}`}
          >
            <div className="h-full w-full bg-gray-300 rounded-t-2xl"></div>
          </div>
        )}
        {props.data["status"] === "completed" && (
          <Link href={`/${pathname}/${props.data["id"]}`}>
            <Image
              src={props.data["thumbnail_link"]}
              alt={props.data["title"]}
              width={312}
              height={312}
              sizes="100vw"
              style={{ width: "100%", height: "100%", objectFit: "cover" }}
              className={`rounded-t-2xl transition-all duration-500 ease-in-out ${
                isLoaded ? "opacity-100" : "opacity-0"
              }`}
              onLoad={() => setIsLoaded(true)}
              priority={true}
            />
          </Link>
        )}
      </div>
      <div className="bg-gray-100 w-full pt-2 pb-3 pl-2 rounded-b-2xl flex">
        <div className="space-y-1 w-[100%]">
          {title_len > 20 && (
            <Tooltip
              label={props.data["title"]}
              className="hidden"
              events={{ hover: true, focus: true, touch: true }}
              color="violet"
              withArrow
            >
              <h1 className="font-semibold text-lg text-black ml-3">{title}</h1>
            </Tooltip>
          )}
          {title_len <= 20 && (
            <h1 className="font-semibold text-base sm:text-lg text-black ml-3">
              {title}
            </h1>
          )}

          <h1 className={`text-xs sm:text-sm ${content_info_css} ml-3`}>
            {content_info}
          </h1>
        </div>
        {props.data["status"] === "completed" && (
          <div className="flex px-3 items-center" id="dropdownButton">
            <DropDown data={props.data} type={props.type} />
          </div>
        )}
      </div>
    </div>
  );
}
