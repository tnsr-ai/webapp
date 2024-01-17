"use client";
import Link from "next/link";
import Image from "next/image";
import { useState, useEffect } from "react";
import { tagColor } from "../content/contentLists/TagsClass";
import { VideoCamera, Photo, SpeakerWave } from "styled-icons/heroicons-solid";

function capitalizeWords(input: string): string[] {
  if (input.includes(",") === false) {
    return [input.charAt(0).toUpperCase() + input.slice(1)];
  }
  const words = input.split(",");
  const capitalizedWords = words.map((word) => {
    const trimmedWord = word.trim();
    if (trimmedWord.includes(" ") === true) {
      return trimmedWord
        .split(" ")
        .map((word) => {
          return word.charAt(0).toUpperCase() + word.slice(1);
        })
        .join(" ");
    }
    return trimmedWord.charAt(0).toUpperCase() + trimmedWord.slice(1);
  });

  return capitalizedWords;
}

export default function JobsCard(props: any) {
  const tags = capitalizeWords(props.data.tags);
  return (
    <div className="mt-4 border border-dashed border-black h-full  rounded-lg grid grid-cols-6">
      <div className="col-span-1 h-full w-full flex flex-col p-2 relative -z-0">
        {/* h-[100%] w-[456px] p-1 relative -z-0 col-span-4 cursor-pointer */}
        <Image
          src={props.data.image}
          alt={props.data.title}
          width={200}
          height={0}
          sizes="100vw"
          style={{ width: "100%", height: "100%", objectFit: "cover" }}
          className="rounded-xl opacity-25"
        />
        <VideoCamera className="w-10 lg:w-12 fill-slate-500 absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2" />
      </div>
      <div className="col-span-3 h-full w-full flex flex-col ">
        <div className="m-2">
          <p className="font-medium">{props.data.title}</p>
          <div className="justify-start items-center gap-1 flex-wrap h-auto w-fit rounded-lg hidden lg:flex">
            {tags.map((tags: string, index: any) => (
              <span className={tagColor[tags]} key={index}>
                {tags}
              </span>
            ))}
          </div>
        </div>
      </div>
      <div className="col-span-1 h-full w-full flex flex-col ">
        <div className="w-full h-full flex justify-center items-center">
          <span className="inline-flex items-center gap-x-1.5 rounded-full bg-yellow-100 px-1.5 py-0.5 text-xs font-medium text-yellow-800">
            <svg
              className="h-1.5 w-1.5 fill-yellow-500"
              viewBox="0 0 6 6"
              aria-hidden="true"
            >
              <circle cx={3} cy={3} r={3} />
            </svg>
            {props.data.status}
          </span>
        </div>
      </div>
      <div className="col-span-1 h-full w-full flex flex-col ">
        <div className="w-full h-full flex justify-center items-center">
          <button
            type="button"
            className="rounded-md bg-red-50 px-3.5 py-2.5 text-sm font-semibold text-red-600 shadow-sm hover:bg-red-100"
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
}
