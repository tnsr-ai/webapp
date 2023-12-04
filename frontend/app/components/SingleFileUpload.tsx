"use client";
import { useEffect, useState } from "react";
import axios from "axios";
import { Grid } from "@mui/material";
import CircularProgress, {
  CircularProgressProps,
} from "@mui/material/CircularProgress";
import Typography from "@mui/material/Typography";
import Box from "@mui/material/Box";
import {
  XMarkIcon,
  XCircleIcon,
  CheckIcon,
  CircleStackIcon,
  CogIcon,
} from "@heroicons/react/20/solid";
import { getCookie } from "cookies-next";
import { usePathname } from "next/navigation";
import { ParallelHasher } from "ts-md5";
import { Tooltip } from "@mantine/core";
import { fileSizeUnits } from "../constants/constants";

export interface UploadableFile {
  file: File;
}

function niceBytes(x: number): string {
  let l = 0,
    n = x;
  while (n >= 1024 && ++l) n /= 1024;
  return `${n.toFixed(2)} ${fileSizeUnits[l]}`;
}

function CircularProgressWithLabel(
  props: CircularProgressProps & { value: number }
) {
  return (
    <Box sx={{ position: "relative", display: "inline-flex" }}>
      <CircularProgress variant="determinate" {...props} />
      <Box
        sx={{
          top: 0,
          left: 0,
          bottom: 0,
          right: 0,
          position: "absolute",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        <Typography
          variant="caption"
          component="div"
          color="text.secondary"
        >{`${Math.round(props.value)}%`}</Typography>
      </Box>
    </Box>
  );
}

export function SingleFileUpload(props: any = null) {
  let title;
  title = props.file.name;
  let title_len = title.length;
  if (title_len > 20) {
    title = title.substring(0, 20) + "...";
  }

  const jwt = getCookie("access_token");
  const acceptedFileext: string[] = [];
  for (let key in props.filetype) {
    acceptedFileext.push(key);
  }

  const pathname = usePathname();
  const [showProgress, setShowProgress] = useState(false);
  const [progress, setProgress] = useState(0);
  const [xhr, setXHR] = useState<XMLHttpRequest>(new XMLHttpRequest());
  const [isCancelled, setIsCancelled] = useState(false);
  const [displayMsg, setDisplayMsg] = useState("");
  const [indexDone, setIndexDone] = useState(false);

  const cancePUT = (xhr: XMLHttpRequest) => {
    setIsCancelled(true);
    xhr.abort();
    setDisplayMsg("Upload Cancelled");
  };

  useEffect(() => {
    if (indexDone === true) {
      props.setVideoUpload(true);
      return;
    }
    let hasher = new ParallelHasher("/md5worker/md5_worker.js");
    const xhr = new XMLHttpRequest();
    setXHR(xhr);
    async function getPutURL(md5_string: string) {
      const data = JSON.stringify({
        filename: props.file.name,
        filetype: props.file.type,
        md5: md5_string,
        filesize: props.file.size,
      });
      const url: string = `${process.env.BASEURL}/upload/generate_presigned_post`;
      try {
        const signedResponse = await axios.post(url, data, {
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${jwt}`,
          },
        });
        if (signedResponse.status === 507) {
          setDisplayMsg("Storage limit exceeded");
          setIsCancelled(true);
          return { detail: "Failed", data: "Storage limit exceeded" };
        }
        if (signedResponse.status != 201) {
          setDisplayMsg("Network Error");
          setIsCancelled(true);
          return { detail: "Failed", data: "Network Error" };
        }
        return await signedResponse.data.data;
      } catch (error: any) {
        return { detail: "Failed", data: error?.response?.data?.detail };
      }
    }

    async function upload(
      xhr: XMLHttpRequest,
      file: File,
      signedResponse: any,
      onProgress: (percent: number) => void,
      md5: string
    ) {
      await uploadFile(xhr, file, signedResponse, onProgress, setDisplayMsg);
      let processType = "";
      if (pathname.includes("video")) {
        processType = "video";
      } else if (pathname.includes("audio")) {
        processType = "audio";
      } else {
        processType = "image";
      }
      const indexData = {
        config: {
          filename: props.file.name,
          indexfilename: signedResponse.filename,
        },
        processtype: processType,
        md5: md5,
        id_related: null,
      };
      setDisplayMsg("Please wait while we index your file");
      try {
        const indexResponse = await IndexData(indexData, jwt as string);
        if (indexResponse?.status !== 201) {
          setDisplayMsg("Error while indexing file");
          setIsCancelled(true);
          setShowProgress(true);
        } else {
          setDisplayMsg("Upload Complete");
        }
      } catch (error: any) {
        setDisplayMsg("Network Error");
      }
    }

    if (props.maxFileSize > props.file.size) {
      if (acceptedFileext.includes(props.file.type)) {
        hasher.hash(props.file).then(async function (result) {
          const signedResponse = await getPutURL(result as string);
          if (signedResponse.detail === "Failed") {
            setDisplayMsg(signedResponse.data);
            setIsCancelled(true);
            setShowProgress(true);
          } else {
            setShowProgress(true);
            await upload(
              xhr,
              props.file,
              signedResponse,
              setProgress,
              result as string
            );
            props.setVideoUpload(true);
          }
        });
      } else {
        setDisplayMsg("File type not valid");
        setIsCancelled(true);
        setShowProgress(true);
      }
    } else {
      setDisplayMsg("File size too large");
      setIsCancelled(true);
      setShowProgress(true);
    }
    setIndexDone(true);
  }, [
    displayMsg,
    showProgress,
    indexDone,
    isCancelled,
    props.file,
    setDisplayMsg,
  ]);

  return (
    <div className="max-w-[1200px] mt-5 m-auto">
      <Grid item className="flex items-start w-[100%] px-5">
        <div className="flex flex-row gap-2 md:gap-4">
          {title_len > 20 && (
            <Tooltip label={props.file.name} className="hidden">
              <h1 className="text-black font-normal text-base md:text-lg flex m-auto">
                {title}
              </h1>
            </Tooltip>
          )}
          {title_len <= 20 && (
            <h1 className="text-black font-normal text-base md:text-lg flex m-auto">
              {title}
            </h1>
          )}
          <h1 className="text-black font-light text-sm flex m-auto">
            {niceBytes(Number(props.file.size))}
          </h1>
          {displayMsg === "Please wait while we index your file" && (
            <div className="flex">
              <CircleStackIcon className="fill-purple-400 h-8 w-8 inline-flex m-auto mr-1 md:mr-2" />
              <h1 className="text-black font-normal text-sm md:text-base inline-flex m-auto">
                {displayMsg}
              </h1>
            </div>
          )}
          {displayMsg === "Upload Complete" && (
            <div className="flex">
              <CheckIcon className="fill-green-600 h-8 w-8 inline-flex m-auto mr-1 md:mr-2" />
              <h1 className="text-black font-normal text-sm md:text-base inline-flex m-auto">
                {displayMsg}
              </h1>
            </div>
          )}
          {isCancelled && (
            <div className="flex">
              <XCircleIcon className="fill-red-600 h-8 w-8 inline-flex m-auto mr-1 md:mr-2" />
              <h1 className="text-black font-normal text-sm md:text-base inline-flex m-auto">
                {displayMsg}
              </h1>
            </div>
          )}
          {showProgress == false && (
            <div className="flex">
              <CogIcon className="fill-purple-400 h-8 w-8 inline-flex m-auto mr-1 md:mr-2" />
              <h1 className="text-black font-normal text-sm md:text-base inline-flex m-auto">
                Processing...
              </h1>
            </div>
          )}
          {showProgress == true && !isCancelled && progress !== 100 && (
            <div className="flex">
              <CircularProgressWithLabel
                value={progress}
                size={50}
                thickness={4.2}
              />
              <button
                type="button"
                key="cancel"
                className="inline-flex h-[80%] m-auto items-center rounded-md border border-transparent bg-purple-600 px-2 text-sm font-medium leading-4 text-white shadow-sm hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2 ml-2"
                onClick={() => cancePUT(xhr)}
                disabled={isCancelled}
              >
                <XMarkIcon
                  className="-ml-0.5 mr-2 h-4 w-4"
                  aria-hidden="true"
                />
                Cancel
              </button>
            </div>
          )}
        </div>
      </Grid>
    </div>
  );
}

async function IndexData(data: any, cookie: string) {
  const url: string = `${process.env.BASEURL}/upload/indexfile`;
  try {
    const response = await axios.post(url, data, {
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${cookie}`,
      },
    });
    return response;
  } catch (error: any) {}
}

function uploadFile(
  xhr: XMLHttpRequest,
  file: File,
  signedUrlJson: any,
  onProgress: (percent: number) => void,
  setDisplayMsg: (msg: string) => void
) {
  const url = signedUrlJson.signed_url;
  const newFile = new File([file], signedUrlJson.filename, { type: file.type });
  return new Promise((resolve, reject) => {
    xhr.open("PUT", url, true);
    xhr.setRequestHeader("Content-Type", newFile.type);
    xhr.setRequestHeader("Content-MD5", signedUrlJson.md5);
    xhr.onload = () => {
      resolve(xhr.status);
    };
    xhr.onerror = (eve) => reject(eve);
    xhr.addEventListener;
    xhr.upload.onprogress = (event) => {
      if (event.lengthComputable) {
        const percent = Math.round((event.loaded / event.total) * 100);
        onProgress(percent);
      }
    };
    xhr.ontimeout = () => {
      reject(new Error("timeout"));
    };
    xhr.send(newFile);
  });
}
