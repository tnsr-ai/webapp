"use client";
import Image from "next/image";
import {
  PlayIcon,
  InformationCircleIcon,
  Bars3Icon,
  BeakerIcon,
} from "@heroicons/react/20/solid";
import VideoPlayer from "./videoPlayer";
import FilterModal from "./filterModal";
import { Menu, Button, Tooltip, Skeleton, Loader } from "@mantine/core";
import { IconBallpen, IconTrash, IconCloudDownload } from "@tabler/icons-react";
import { tagColor } from "./TagsClass";
import React, { useState, useEffect } from "react";
import { usePathname } from "next/navigation";
import Link from "next/link";
import { Toaster, toast } from "sonner";
import { getCookie } from "cookies-next";
import RenamePrompt from "../../content/contentCards/RenameModal";
import { infinity } from "ldrs";
import { useJobsConfig } from "../../api/index";
import Error from "../../components/ErrorTab";
import { useQueryClient } from "@tanstack/react-query";
import ContentDeletePrompt from "../../content/contentCards/ContentDeleteModal";

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

export function ContentComponent(props: any) {
  const queryClient = useQueryClient();
  const jobsConfig = useJobsConfig();
  infinity.register();
  const [jobsParams, setJobsParams] = useState(undefined);
  const [userTier, setUserTier] = useState("free");
  const [tierConfig, setTierConfig] = useState();
  const pathname = usePathname().split("/")[1];
  const [videoPlayer, setVideoPlayer] = useState(false);
  const [filterShow, setFilterShow] = useState(false);
  const [disableDelete, setDisableDelete] = useState(false);
  const [renamePrompt, setRenamePrompt] = useState(false);
  const [delPrompt, setDelPrompt] = useState(false);
  const tags = capitalizeWords(props.data.tags);
  let title;
  title = props.data["title"];
  let title_len = title.length;
  if (title_len > 15) {
    title = title.substring(0, 15) + "...";
  }
  let fps = parseFloat(props.data.fps).toFixed(2);
  const [isLoaded, setIsLoaded] = useState(false);
  useEffect(() => {
    if (props.data.tags === "Original") {
      setDisableDelete(true);
    }
  }, [disableDelete, props.data.tags]);

  function getCurrentDimension() {
    return {
      width: window.innerWidth,
      height: window.innerHeight,
    };
  }
  function convertToSeconds(timeString: string) {
    // Split the time string by colon
    const parts = timeString.split(":");

    // Extract hours, minutes, and seconds from the array
    const hours = parseInt(parts[0], 10);
    const minutes = parseInt(parts[1], 10);
    const seconds = parseInt(parts[2], 10);

    // Calculate total seconds
    const totalSeconds = hours * 3600 + minutes * 60 + seconds;

    return totalSeconds;
  }
  function checkContentTier() {
    if (props.data.content_type === "video") {
      const width = Number(props.data.resolution.split("x")[0]);
      const height = Number(props.data.resolution.split("x")[1]);
      const tier_width = tierConfig?.[userTier][pathname]["width"] || 1920;
      const tier_height = tierConfig?.[userTier][pathname]["height"] || 1080;
      if (width > tier_width || height > tier_height) {
        toast.error(
          `Content resolution exceeds ${capitalizeWords(userTier)} tier limit`
        );
        return;
      }
      setFilterShow(true);
    }
    if (props.data.content_type === "audio") {
      const duration = convertToSeconds(props.data.duration);
      let tier_duration = tierConfig?.[userTier][pathname]["duration"] || 300;
      if (tier_duration === -1) {
        tier_duration = Infinity;
      }
      if (duration > tier_duration) {
        toast.error(
          `Content duration exceeds ${capitalizeWords(userTier)} tier limit`
        );
        return;
      }
      setFilterShow(true);
    }

    if (props.data.content_type === "image") {
      const width = Number(props.data.resolution.split("x")[0]);
      const height = Number(props.data.resolution.split("x")[1]);
      const tier_width = tierConfig?.[userTier][pathname]["width"] || 1920;
      const tier_height = tierConfig?.[userTier][pathname]["height"] || 1080;
      if (width > tier_width || height > tier_height) {
        toast.error(
          `Content resolution exceeds ${capitalizeWords(userTier)} tier limit`
        );
        return;
      }
      setFilterShow(true);
    }
  }
  const [screenSize, setScreenSize] = useState(getCurrentDimension());

  const downloadContent = async () => {
    const jwt = getCookie("access_token");
    const url = `${process.env.BASEURL}/content/download_content/?content_id=${props.data.id}&content_type=${props.type}`;
    const response = await fetch(url, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${jwt}`,
      },
    });
    if (!response.ok) {
      toast.error("Download failed");
      return;
    }
    const data = await response.json();
    const presigned_url = data.data;
    const toastID = toast("");
    toast.loading("Downloading...", { id: toastID });
    const xhr = new XMLHttpRequest();
    xhr.responseType = "blob";
    xhr.onprogress = function (event) {
      if (event.lengthComputable) {
        const percentComplete = Math.round((event.loaded / event.total) * 100);
        toast.loading(`Downloading... ${percentComplete}%`, {
          id: toastID,
          action: {
            label: "Cancel",
            onClick: () => xhr.abort(),
          },
        });
      }
    };
    const promise = (xhr: any) =>
      new Promise((resolve, reject) => {
        xhr.open("GET", presigned_url, true);
        xhr.responseType = "blob";
        xhr.onload = () => resolve(xhr.response);
        xhr.onerror = () => reject(xhr.statusText);
        xhr.send();
      });

    toast.promise(promise(xhr), {
      success: () => {
        const blob = xhr.response;
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = props.data["title"];
        document.body.appendChild(a);
        a.click();
        a.remove();
        window.URL.revokeObjectURL(url);
        const downloadCompleteURL = `${process.env.BASEURL}/content/download_complete/?content_id=${props.data.id}&content_type=${props.type}`;
        fetch(downloadCompleteURL, {
          method: "GET",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${jwt}`,
          },
        });
        return "Downloaded";
      },
      error: "Download failed",
      action: {
        label: "Cancel",
        onClick: () => xhr.abort(),
      },
      id: toastID,
    });

    xhr.onreadystatechange = function () {
      if (xhr.readyState === 4) {
        if (xhr.status === 200) {
          toast.dismiss(toastID);
        } else {
          toast.error("Download failed", { id: toastID });
        }
      }
    };
  };

  useEffect(() => {
    if (jobsConfig.isSuccess && jobsParams === undefined) {
      queryClient.invalidateQueries();
      setJobsParams(JSON.parse(jobsConfig.data.data));
      setUserTier(jobsConfig.data.tier);
      setTierConfig(JSON.parse(jobsConfig.data.tier_config));
    }
  }, [jobsConfig, jobsParams, pathname]);

  const videoInfo = (
    <div
      id="info"
      className="col-span-9 row-span-2  md:col-span-4 flex justify-center items-center w-full"
    >
      <div className="h-[100%] w-[456px] p-1 relative -z-0 col-span-4 cursor-pointer">
        {!isLoaded && <Skeleton style={{ height: "100%" }} />}
        <Image
          src={props.data["thumbnail_link"]}
          alt={title}
          width={200}
          height={0}
          sizes="100vw"
          style={{ width: "100%", height: "100%", objectFit: "cover" }}
          className={`rounded-xl ${
            props.data.status === "processing" ? "opacity-45" : ""
          }`}
          onLoad={() => setIsLoaded(true)}
          onClick={() => {
            setVideoPlayer(true);
          }}
        />
        {props.data.status === "completed" && (
          <PlayIcon
            className="w-10 lg:w-12 fill-white absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2"
            onClick={() => {
              setVideoPlayer(true);
            }}
          />
        )}
        {props.data.status === "processing" && (
          <BeakerIcon className="w-10 lg:w-12 fill-slate-600 absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2" />
        )}
        <VideoPlayer
          videoPlayer={videoPlayer}
          setVideoPlayer={setVideoPlayer}
          link={props.data["content_link"]}
          type={pathname}
        />
      </div>
      <div className="py-1 pl-2 w-[100%] col-span-4" id="contentInfo">
        {title_len > 15 && (
          <Tooltip
            label={props.data["title"]}
            className="hidden"
            events={{ hover: true, focus: true, touch: true }}
            color="violet"
            withArrow
          >
            <h1 className="font-bold text-base md:text-lg lg:text-xl">
              {title}
            </h1>
          </Tooltip>
        )}
        {title_len <= 15 && (
          <h1 className="font-bold text-base md:text-lg lg:text-xl whitespace-nowrap">
            {title}
          </h1>
        )}
        <div
          className={`pt-0.5 space-x-2 ${
            props.data.status === "processing" ? "hidden" : "flex"
          }`}
        >
          <p className="text-sm xl:text-lg whitespace-nowrap">
            {props.data.size}
          </p>
          <p className="whitespace-nowrap text-sm xl:text-lg">{fps} FPS</p>
        </div>
        <div className="flex-row space-y-[1px] pt-0.5">
          <p className="whitespace-nowrap text-sm xl:text-lg">
            {props.data.duration}
          </p>

          <p className="whitespace-nowrap text-sm xl:text-lg">
            {props.data.resolution}
          </p>
        </div>
      </div>
      <div className="w-full h-full col-span-1 flex md:hidden">
        <div className="w-[80%] flex justify-end items-center">
          <Tooltip
            label={
              <div className="flex justify-center items-center gap-1 flex-wrap h-auto w-fit rounded-lg border-2 border-black border-dotted p-1">
                {tags.map((tags: string, index: any) => (
                  <span className={tagColor[tags]} key={index}>
                    {tags}
                  </span>
                ))}
              </div>
            }
            className="hidden w-fit"
            color="gray.1"
            events={{ hover: true, focus: true, touch: true }}
            withArrow
            position="bottom-end"
          >
            <InformationCircleIcon className="w-5 md:w-6 block md:hidden" />
          </Tooltip>
        </div>
      </div>
    </div>
  );

  const audioInfo = (
    <div
      id="info"
      className="col-span-9 row-span-2  md:col-span-4 flex justify-center items-center w-full"
    >
      <div className="h-[100%] w-[456px] p-1 relative -z-0 col-span-4 cursor-pointer">
        {!isLoaded && <Skeleton style={{ height: "100%" }} />}
        <Image
          src={props.data["thumbnail_link"]}
          alt={title}
          width={200}
          height={0}
          sizes="100vw"
          style={{ width: "100%", height: "100%", objectFit: "cover" }}
          className={`rounded-xl ${
            props.data.status === "processing" ? "opacity-45" : ""
          }`}
          onLoad={() => setIsLoaded(true)}
          onClick={() => {
            setVideoPlayer(true);
          }}
        />
        {props.data.status === "completed" && (
          <PlayIcon
            className="w-10 lg:w-12 fill-white absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2"
            onClick={() => {
              setVideoPlayer(true);
            }}
          />
        )}
        {props.data.status === "processing" && (
          <BeakerIcon className="w-10 lg:w-12 fill-slate-600 absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2" />
        )}
        <VideoPlayer
          videoPlayer={videoPlayer}
          setVideoPlayer={setVideoPlayer}
          link={props.data["content_link"]}
          type={pathname}
        />
      </div>
      <div className="py-1 pl-2 w-[100%] col-span-4" id="contentInfo">
        {title_len > 15 && (
          <Tooltip
            label={props.data["title"]}
            className="hidden"
            events={{ hover: true, focus: true, touch: true }}
            color="violet"
            withArrow
          >
            <h1 className="font-bold text-base md:text-lg lg:text-xl">
              {title}
            </h1>
          </Tooltip>
        )}
        {title_len <= 15 && (
          <h1 className="font-bold text-base md:text-lg lg:text-xl whitespace-nowrap">
            {title}
          </h1>
        )}
        <div
          className={`pt-0.5 space-x-2 ${
            props.data.status === "processing" ? "hidden" : "flex"
          }`}
        >
          <p className="text-sm xl:text-lg whitespace-nowrap">
            {props.data.size}
          </p>
          <p className="whitespace-nowrap text-sm xl:text-lg">
            {props.data.hz} HZ
          </p>
        </div>
        <div className="flex-row space-y-[1px] pt-0.5">
          <p className="whitespace-nowrap text-sm xl:text-lg">
            {props.data.duration}
          </p>

          <p className="whitespace-nowrap text-sm xl:text-lg">
            {props.data.resolution}
          </p>
        </div>
      </div>
      <div className="w-full h-full col-span-1 flex md:hidden">
        <div className="w-[80%] flex justify-end items-center">
          <Tooltip
            label={
              <div className="flex justify-center items-center gap-1 flex-wrap h-auto w-fit rounded-lg border-2 border-black border-dotted p-1">
                {tags.map((tags: string, index: any) => (
                  <span className={tagColor[tags]} key={index}>
                    {tags}
                  </span>
                ))}
              </div>
            }
            className="hidden w-fit"
            color="gray.1"
            events={{ hover: true, focus: true, touch: true }}
            withArrow
            position="bottom-end"
          >
            <InformationCircleIcon className="w-5 md:w-6 block md:hidden" />
          </Tooltip>
        </div>
      </div>
    </div>
  );

  const imageInfo = (
    <div
      id="info"
      className="col-span-9 row-span-2  md:col-span-4 flex justify-center items-center w-full"
    >
      <div className="h-[100%] w-[456px] p-1 relative -z-0 col-span-4 cursor-pointer">
        {!isLoaded && <Skeleton style={{ height: "100%" }} />}
        {props.data.status === "completed" && (
          <Link href={props.data["content_link"]} target="_blank">
            <Image
              src={props.data["thumbnail_link"]}
              alt={title}
              width={200}
              height={0}
              sizes="100vw"
              style={{ width: "100%", height: "100%", objectFit: "cover" }}
              className={`rounded-xl ${
                props.data.status === "processing" ? "opacity-45" : ""
              }`}
              onLoad={() => setIsLoaded(true)}
              onClick={() => {
                setVideoPlayer(true);
              }}
            />
          </Link>
        )}
        {props.data.status === "processing" && (
          <React.Fragment>
            <Image
              src={props.data["thumbnail_link"]}
              alt={title}
              width={200}
              height={0}
              sizes="100vw"
              style={{ width: "100%", height: "100%", objectFit: "cover" }}
              className={`rounded-xl ${
                props.data.status === "processing" ? "opacity-45" : ""
              }`}
              onLoad={() => setIsLoaded(true)}
              onClick={() => {
                setVideoPlayer(true);
              }}
            />
            {props.data.status === "processing" && (
              <BeakerIcon className="w-10 lg:w-12 fill-slate-600 absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2" />
            )}
          </React.Fragment>
        )}
      </div>
      <div className="py-1 pl-2 w-[100%] col-span-4" id="contentInfo">
        {title_len > 15 && (
          <Tooltip
            label={props.data["title"]}
            className="hidden"
            events={{ hover: true, focus: true, touch: true }}
            color="violet"
            withArrow
          >
            <h1 className="font-bold text-base md:text-lg lg:text-xl">
              {title}
            </h1>
          </Tooltip>
        )}
        {title_len <= 15 && (
          <h1 className="font-bold text-base md:text-lg lg:text-xl whitespace-nowrap">
            {title}
          </h1>
        )}
        <div
          className={`pt-0.5 space-x-2 ${
            props.data.status === "processing" ? "hidden" : "flex"
          }`}
        >
          <p className="text-sm xl:text-lg whitespace-nowrap">
            {props.data.size}
          </p>
        </div>
        <div className="flex-row space-y-[1px] pt-0.5">
          <p className="whitespace-nowrap text-sm xl:text-lg">
            {props.data.duration}
          </p>

          <p className="whitespace-nowrap text-sm xl:text-lg">
            {props.data.resolution}
          </p>
        </div>
      </div>
      <div className="w-full h-full col-span-1 flex md:hidden">
        <div className="w-[80%] flex justify-end items-center">
          <Tooltip
            label={
              <div className="flex justify-center items-center gap-1 flex-wrap h-auto w-fit rounded-lg border-2 border-black border-dotted p-1">
                {tags.map((tags: string, index: any) => (
                  <span className={tagColor[tags]} key={index}>
                    {tags}
                  </span>
                ))}
              </div>
            }
            className="hidden w-fit"
            color="gray.1"
            events={{ hover: true, focus: true, touch: true }}
            withArrow
            position="bottom-end"
          >
            <InformationCircleIcon className="w-5 md:w-6 block md:hidden" />
          </Tooltip>
        </div>
      </div>
    </div>
  );

  useEffect(() => {}), [screenSize];
  return (
    <div id={props.data.id}>
      <div className="max-w-[1500px] m-auto">
        {jobsConfig.isLoading === true && (
          <div className="flex mt-10 md:mt-5 justify-center">
            <Loader color="grape" variant="bars" />
          </div>
        )}

        {jobsConfig.isSuccess === true && (
          <div className="w-[100%]">
            {screenSize.width < 1030 && (
              <Toaster position="bottom-right" richColors />
            )}
            {screenSize.width > 1030 && (
              <Toaster position="top-right" richColors />
            )}
            <div className="grid grid-rows-3 grid-cols-6 md:grid-cols-9 md:grid-rows-1 max-w-[1500px] h-[200px] hover:bg-gray-50 mx-3 rounded-xl border-solid border-2 p-1">
              {(pathname === "image" && imageInfo) ||
                (pathname === "audio" && audioInfo) ||
                (pathname === "video" && videoInfo)}

              <div
                id="tags"
                className="col-span-1 row-span-2 md:col-span-3 md:flex justify-center items-center hidden"
              >
                <div className="flex justify-center items-center gap-1 flex-wrap h-auto">
                  {tags.map((tags: string, index: any) => (
                    <span className={tagColor[tags]} key={index}>
                      {tags}
                    </span>
                  ))}
                </div>
              </div>
              <div
                id="process"
                className="col-span-6 md:col-span-2 row-span-1 flex space-x-3 justify-center items-center"
              >
                {props.data.status === "completed" && (
                  <div className="flex justify-center items-center">
                    <Button
                      variant="outline"
                      color="violet"
                      onClick={() => {
                        checkContentTier();
                      }}
                    >
                      Process
                    </Button>
                    <FilterModal
                      filterShow={filterShow}
                      setFilterShow={setFilterShow}
                      id={props.data.id}
                      content_data={props.data}
                      model_config={jobsParams}
                      user_tier={userTier}
                      tier_config={tierConfig}
                    />
                  </div>
                )}
                <div className="flex justify-center items-center">
                  {props.data.status === "completed" && (
                    <button>
                      <Menu shadow="md" width={200} withArrow>
                        <Menu.Target>
                          <Bars3Icon className="w-[28px] cursor-pointer" />
                        </Menu.Target>

                        <Menu.Dropdown>
                          <Menu.Item
                            icon={<IconCloudDownload size={14} />}
                            onClick={downloadContent}
                          >
                            Download
                          </Menu.Item>
                          <Menu.Item
                            icon={<IconBallpen size={14} />}
                            onClick={() => {
                              setRenamePrompt(true);
                            }}
                          >
                            Rename
                          </Menu.Item>

                          <Menu.Item
                            color="red"
                            icon={<IconTrash size={14} />}
                            disabled={disableDelete}
                            onClick={() => {
                              setDelPrompt(true);
                            }}
                          >
                            Delete
                          </Menu.Item>
                        </Menu.Dropdown>
                      </Menu>
                    </button>
                  )}
                  {props.data.status === "processing" && (
                    <div className=" cursor-pointer">
                      <Link
                        href={"/jobs"}
                        className="flex flex-col justify-center items-center"
                      >
                        <l-infinity
                          size="35"
                          stroke="3.5"
                          speed="0.9"
                          color="purple"
                        />
                        <p className="text-center font-medium text-black mt-2">
                          Processing...
                        </p>
                      </Link>
                    </div>
                  )}
                </div>
              </div>
            </div>
            <RenamePrompt
              renamePrompt={renamePrompt}
              setRenamePrompt={setRenamePrompt}
              id={props.data.id}
              type={props.type}
              title={props.data.title}
              project={false}
            />
            <ContentDeletePrompt
              delPrompt={delPrompt}
              setDelPrompt={setDelPrompt}
              id={props.data.id}
              type={props.type}
              title={props.data.title}
            />
          </div>
        )}

        {jobsConfig.isError === true && <Error />}
      </div>
    </div>
  );
}
