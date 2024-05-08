"use client";
import Link from "next/link";
import Image from "next/image";
import { useState, useEffect } from "react";
import { tagColor } from "../content/contentLists/TagsClass";
import { VideoCamera, Photo, SpeakerWave } from "styled-icons/heroicons-solid";
import { Progress, Loader } from "@mantine/core";

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

function capitalizeFirstChar(word: string) {
  if (!word) return "";
  return word.charAt(0).toUpperCase() + word.slice(1);
}

function epochToDate(time: number) {
  const date = new Date(time * 1000);
  return date.toLocaleString("en-GB", { hour12: false });
}

function statusBadge(status: string) {
  if (status === "Processing") {
    return (
      <span className="inline-flex items-center gap-x-1.5 rounded-full bg-yellow-100 px-1.5 py-0.5 text-xs font-medium text-yellow-800">
        <svg
          className="h-1.5 w-1.5 fill-yellow-500"
          viewBox="0 0 6 6"
          aria-hidden="true"
        >
          <circle cx={3} cy={3} r={3} />
        </svg>
        {capitalizeFirstChar(status)}
      </span>
    );
  }
  if (status === "Loading") {
    return (
      <span className="inline-flex items-center gap-x-1.5 rounded-full bg-blue-100 px-1.5 py-0.5 text-xs font-medium text-blue-800">
        <svg
          className="h-1.5 w-1.5 fill-blue-500"
          viewBox="0 0 6 6"
          aria-hidden="true"
        >
          <circle cx={3} cy={3} r={3} />
        </svg>
        {capitalizeFirstChar(status)}
      </span>
    );
  }
  if (status === "Completed") {
    return (
      <span className="inline-flex items-center gap-x-1.5 rounded-full bg-green-100 px-1.5 py-0.5 text-xs font-medium text-green-800">
        <svg
          className="h-1.5 w-1.5 fill-green-500"
          viewBox="0 0 6 6"
          aria-hidden="true"
        >
          <circle cx={3} cy={3} r={3} />
        </svg>
        {capitalizeFirstChar(status)}
      </span>
    );
  }
  if (status === "Failed" || status === "Cancelled") {
    return (
      <span className="inline-flex items-center gap-x-1.5 rounded-full bg-red-100 px-1.5 py-0.5 text-xs font-medium text-red-800">
        <svg
          className="h-1.5 w-1.5 fill-red-500"
          viewBox="0 0 6 6"
          aria-hidden="true"
        >
          <circle cx={3} cy={3} r={3} />
        </svg>
        {capitalizeFirstChar(status)}
      </span>
    );
  }
}

export default function JobsCard(props: any) {
  const tags = capitalizeWords(props.data.content_detail["tags"]);
  const colorTag = tagColor[capitalizeFirstChar(props.data.job_status)];
  return (
    <div className="ml-2 md:ml-0 mr-2 md:mr-0">
      <div className="mt-4 border border-dashed border-black h-full  rounded-lg grid grid-cols-6">
        <div className="col-span-1 h-full w-full max-h-[125px] flex flex-col p-2 relative -z-0">
          <Image
            src={props.data.content_detail["thumbnail"]}
            alt={props.data.content_detail["title"]}
            width={200}
            height={0}
            sizes="100vw"
            style={{ width: "100%", height: "100%", objectFit: "cover" }}
            className="rounded-xl opacity-25"
          />
          {props.data.job_type === "video" && (
            <VideoCamera className="w-8 md:w-10 lg:w-12 fill-slate-500 absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2" />
          )}
          {props.data.job_type === "audio" && (
            <SpeakerWave className="w-8 md:w-10 lg:w-12 fill-slate-500 absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2" />
          )}
          {props.data.job_type === "image" && (
            <Photo className="w-8 md:w-10 lg:w-12 fill-slate-500 absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2" />
          )}
        </div>
        <div className="col-span-3 h-full w-full flex flex-col justify-center">
          <div className="m-2">
            <p className="font-medium">{props.data.content_detail["title"]}</p>
            <p className="font-light text-xs my-1">
              {`Started at - ${epochToDate(
                props.data.content_detail["created_at"]
              )}`}
            </p>

            {props.data.content_detail["status"] === "completed" && (
              <p className="font-light text-xs my-1">
                {`Finished at - ${epochToDate(
                  props.data.content_detail["updated_at"]
                )}`}
              </p>
            )}
            <div className="justify-start items-center gap-1 flex-wrap h-auto w-fit rounded-lg hidden lg:flex">
              {tags.map((tags: string, index: any) => (
                <span className={tagColor[tags]} key={index}>
                  {tags}
                </span>
              ))}
            </div>
            <div className="mt-1">
              <p className="font-light text-xs my-1">
                {capitalizeFirstChar(status)} -{" "}
                <span className="font-semibold text-purple-500">
                  {"Super Resolution"}
                </span>
              </p>
              <Progress color="grape" value={25} striped animate />
            </div>
          </div>
        </div>
        <div className="col-span-1 h-full w-full flex flex-col ">
          <div className="w-full h-full flex justify-center items-center">
            {statusBadge(props.data.job_status)}
          </div>
        </div>
        <div className="col-span-1 h-full w-full flex flex-col ">
          <div
            className={`w-full h-full justify-center items-center ${
              props.data.content_detail["status"] === "processing"
                ? "flex"
                : "hidden"
            }`}
          >
            <button
              type="button"
              className="rounded-md bg-red-50 px-1 md:px-3.5 py-1 md:py-2.5 text-xs font-semibold text-red-600 shadow-sm hover:bg-red-100"
            >
              Cancel
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
