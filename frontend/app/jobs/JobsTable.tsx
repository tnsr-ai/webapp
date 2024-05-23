"use client";
import { useState, useEffect, useRef } from "react";
import JobsCard from "./jobsCard";
import { useQueryClient } from "@tanstack/react-query";
import { useGetJobs } from "../api";
import { Loader } from "@mantine/core";
import Error from "../components/ErrorTab";
import Image from "next/image";
import { getCookie, setCookie } from "cookies-next";
import useWebSocket, { ReadyState } from "react-use-websocket";

export default function JobsTable() {
  const cookieKey = "all_jobs";
  const browserData =
    getCookie(cookieKey) ||
    '{"key": -1, "startPage": 1, "endPage": 1, "totalPage": 0, "offset": 0, "prevPage": true, "nextPage": true}';
  const pageJSON = JSON.parse(browserData as string);
  const [jobType, setJobType] = useState("active");
  const [noJobsText, setNoJobsText] = useState(
    "Your job queue is empty – time to change that. Create a job to begin!"
  );

  const limit = 5;
  const [offset, setOffset] = useState(0);

  const [startPage, setStartPage] = useState(pageJSON.startPage);
  const [endPage, setEndPage] = useState(pageJSON.endPage);
  const [totalPage, setTotalPage] = useState(pageJSON.totalPage);
  const [prevPage, setPrevPage] = useState(pageJSON.prevPage);
  const [nextPage, setNextPage] = useState(pageJSON.nextPage);

  const getJobs = useGetJobs(jobType, limit, offset);

  const disabled = true;
  const enabled = false;

  // websocket connection -
  const ws_url = `${process.env.BASEURL}/jobs/ws`
    .replace("http", "ws")
    .replace("https", "wss");

  const { sendJsonMessage, lastJsonMessage, readyState } = useWebSocket(
    ws_url,
    {
      share: true,
      shouldReconnect: () => true,
    }
  );

  const handleBtnChange = (type: string) => {
    getJobs.refetch();
    setJobType(type);
  };

  const nextData = () => {
    setOffset(offset + limit);
    setStartPage(startPage + limit);
    setPrevPage(enabled);
    if (endPage + limit >= totalPage) {
      setEndPage(totalPage);
    } else {
      setEndPage(endPage + limit);
    }
  };

  const prevData = () => {
    setOffset(offset - limit);
    setNextPage(enabled);
    if (startPage - limit <= 1) {
      setStartPage(1);
      pageJSON.prevPage = false;
      setPrevPage(disabled);
    } else {
      setStartPage(startPage - limit);
    }
    if (endPage - limit <= limit) {
      setEndPage(limit);
    } else {
      setEndPage(endPage - limit);
    }
  };

  useEffect(() => {
    if (getJobs.isSuccess) {
      var jobID: any[] = [];
      getJobs.data.data.forEach((data: any) => {
        jobID.push(data.job_id as number);
      });
    }
  }, [readyState, getJobs.isSuccess, getJobs.data]);

  useEffect(() => {
    if (jobType === "active") {
      setNoJobsText(
        "Your job queue is empty – time to change that. Create a job to begin!"
      );
    } else {
    }
  }, [
    jobType,
    totalPage,
    startPage,
    endPage,
    totalPage,
    limit,
    offset,
    prevPage,
    nextPage,
  ]);

  useEffect(() => {
    if (
      getJobs.isSuccess === true &&
      getJobs.isFetched === true &&
      jobType === "past"
    ) {
      setTotalPage(getJobs.data.total);
      if (getJobs.data.total <= limit) {
        setEndPage(getJobs.data.total);
        setNextPage(disabled);
      } else {
        setEndPage(startPage + limit - 1);
        setNextPage(enabled);
      }
      if (endPage >= totalPage) {
        setEndPage(totalPage);
        setNextPage(disabled);
      }
    }
  });

  const isLoading =
    jobType === "active" ? getJobs.isLoading : getJobs.isLoading;
  const isError = jobType === "active" ? getJobs.isError : getJobs.isError;

  return (
    <div>
      <div>
        <div className="sm:flex sm:items-center">
          <div className="sm:flex-auto ml-2">
            <h1 className="text-2xl font-semibold ml-5 text-black">Jobs</h1>
          </div>
        </div>
        <div className="space-x-2 flex justify-end mr-5 pr-5">
          <button
            type="button"
            className={`rounded-full px-4 py-2.5 text-sm font-semibold text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 hover:bg-gray-100 ${
              jobType === "active"
                ? "bg-purple-100 text-purple-600"
                : "bg-white text-black"
            }`}
            onClick={() => {
              handleBtnChange("active");
            }}
          >
            Active
          </button>
          <button
            type="button"
            className={`rounded-full px-4 py-2.5 text-sm font-semibold text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 hover:bg-gray-100 ${
              jobType === "past"
                ? "bg-purple-100 text-purple-600"
                : "bg-white text-black"
            }`}
            onClick={() => {
              handleBtnChange("past");
            }}
          >
            All
          </button>
        </div>
      </div>
      {isLoading && (
        <div className="w-full h-full flex justify-center items-center">
          <Loader color="grape" variant="bars" />
        </div>
      )}
      {getJobs.data && getJobs.data?.data.length > 0 && (
        <div className="px-4 sm:px-6 lg:px-8">
          <div className="mt-1 flex flex-col">
            <div className="-my-2 -mx-4 overflow-x-auto sm:-mx-6 lg:-mx-8">
              <div className="inline-block min-w-full py-2 align-middle md:px-6 lg:px-8">
                <div className="">
                  <div className="flex flex-col space-y-5">
                    {getJobs.data?.data.map((job: any, index: any) => (
                      <JobsCard
                        data={job}
                        key={index}
                        sendJsonMessage={sendJsonMessage}
                        lastJsonMessage={lastJsonMessage}
                        readyState={readyState}
                        allBtn={jobType === "past"}
                      />
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>
          <div className="mt-5">
            {getJobs.data?.total > limit && (
              <div className="flex flex-col items-center">
                <span className="text-sm text-black ">
                  Showing items{" "}
                  <span className="font-semibold text-black">{startPage}</span>{" "}
                  to <span className="font-semibold text-black">{endPage}</span>{" "}
                  of{" "}
                  <span className="font-semibold text-black">{totalPage}</span>{" "}
                </span>
                <div className="inline-flex mt-2 xs:mt-0 gap-x-2">
                  <button
                    className="flex items-center justify-center px-4 h-10 text-base font-medium text-white bg-purple-600 rounded-lg hover:bg-purple-500 disabled:bg-purple-300"
                    disabled={prevPage}
                    onClick={prevData}
                    id="prev_button"
                  >
                    <svg
                      className="w-3.5 h-3.5 mr-2"
                      aria-hidden="true"
                      xmlns="http://www.w3.org/2000/svg"
                      fill="none"
                      viewBox="0 0 14 10"
                    >
                      <path
                        stroke="currentColor"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth="2"
                        d="M13 5H1m0 0 4 4M1 5l4-4"
                      />
                    </svg>
                    Prev
                  </button>
                  <button
                    className="flex items-center justify-center px-4 h-10 text-base font-medium text-white bg-purple-600 border-0 border-l rounded-lg hover:bg-purple-500 disabled:bg-purple-300"
                    disabled={nextPage}
                    onClick={nextData}
                    id="next_button"
                  >
                    Next
                    <svg
                      className="w-3.5 h-3.5 ml-2"
                      aria-hidden="true"
                      xmlns="http://www.w3.org/2000/svg"
                      fill="none"
                      viewBox="0 0 14 10"
                    >
                      <path
                        stroke="currentColor"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth="2"
                        d="M1 5h12m0 0L9 1m4 4L9 9"
                      />
                    </svg>
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
      {getJobs.data && getJobs.data?.data.length === 0 && (
        <div className="flex flex-col justify-center items-center">
          <div className="min-w-[250px]">
            <Image
              src="/assets/no_jobs.png"
              width={0}
              height={0}
              sizes="100vw"
              alt={"nojob"}
              style={{ width: "100%", height: "100%", objectFit: "cover" }}
              className={`rounded-t-2xl transition-all duration-500 ease-in-out`}
              priority={true}
            ></Image>
          </div>
          <p className="text-black font-medium text-lg md:text-xl text-center">
            {`${noJobsText}`}
          </p>
        </div>
      )}
      {isError && <Error />}
    </div>
  );
}
