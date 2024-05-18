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

interface Jobs {
  detail: string;
  data: [];
  total: number | 0;
}

export default function JobsTable() {
  const cookieKey = "pastjobs";
  const browserData =
    getCookie(cookieKey) ||
    '{"key": -1, "startPage": 1, "endPage": 1, "totalPage": 0, "offset": 0, "prevPage": true, "nextPage": true}';
  const pageJSON = JSON.parse(browserData as string);
  const [call, setCall] = useState("");
  const [activeBtn, setActiveBtn] = useState(true);
  const [allBtn, setAllBtn] = useState(false);
  const [jobsData, setJobsData] = useState<Jobs | null>(null);
  const [jobType, setJobType] = useState("active");
  const limit = 5;
  const [offset, setOffset] = useState(0);
  const [noJobsText, setNoJobsText] = useState(
    "Your job queue is empty – time to change that. Create a job to begin!"
  );

  pageJSON.startPage = 1;
  pageJSON.endPage = 1;
  pageJSON.totalPage = 0;
  pageJSON.offset = 0;
  pageJSON.prevPage = true;
  pageJSON.nextPage = true;

  const [startPage, setStartPage] = useState(pageJSON.startPage);
  const [endPage, setEndPage] = useState(pageJSON.endPage);
  const [totalPage, setTotalPage] = useState(pageJSON.totalPage);
  const [prevPage, setPrevPage] = useState(pageJSON.prevPage);
  const [nextPage, setNextPage] = useState(pageJSON.nextPage);

  const disabled = true;
  const enabled = false;
  const [btnClicked, setBtnClicked] = useState(false);

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

  const nextData = () => {
    setOffset(offset + limit);
    setStartPage(startPage + limit);
    setPrevPage(enabled);
    if (endPage + limit >= totalPage) {
      setEndPage(totalPage);
    } else {
      setEndPage(endPage + limit);
    }
    setBtnClicked(true);
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
    setBtnClicked(true);
  };

  const getJobs = useGetJobs(jobType, limit, offset);

  useEffect(() => {
    if (getJobs.isSuccess) {
      var jobID: any[] = [];
      getJobs.data.data.forEach((data: any) => {
        jobID.push(data.job_id as number);
      });
    }
  }, [readyState, getJobs.isSuccess, getJobs.data]);

  useEffect(() => {
    if (activeBtn && call != "active") {
      getJobs.refetch();
      if (getJobs.isSuccess) {
        setCall("active");
        setJobsData(getJobs.data);
      } else {
        setJobsData(null);
      }
    }
    if (allBtn && call != "past") {
      getJobs.refetch();
      if (getJobs.isSuccess) {
        setCall("past");
        setJobsData(getJobs.data);
        setTotalPage(jobsData?.total);
        if ((jobsData?.total as number) <= limit) {
          setEndPage(jobsData?.total);
          setNextPage(disabled);
        } else {
          setEndPage(startPage + limit - 1);
          setNextPage(enabled);
        }
        if (endPage >= totalPage) {
          setEndPage(totalPage);
          setNextPage(disabled);
        }
        var cookieJSON = {
          startPage: startPage,
          endPage: endPage,
          totalPage: totalPage,
          offset: offset,
          prevPage: prevPage,
          nextPage: nextPage,
        };
        setCookie("pastjobs", JSON.stringify(cookieJSON), {
          maxAge: 60 * 60 * 24,
        });
        if (btnClicked === true) {
          const nextBtn = document.getElementById("next_button");
          const nextBtnOffset = nextBtn?.offsetTop;
          window.scrollTo({ top: nextBtnOffset, behavior: "instant" });
        }
      } else {
        setJobsData(null);
      }
    }
  }, [getJobs, activeBtn, allBtn, getJobs.data, jobsData]);

  const handleActiveClick = () => {
    setActiveBtn(true);
    setAllBtn(false);
    setJobType("active");
    setNoJobsText(
      "Your job queue is empty – time to change that. Create a job to begin!"
    );
  };

  const handleAllClick = () => {
    getJobs.refetch();
    setActiveBtn(false);
    setAllBtn(true);
    setJobType("past");
    setNoJobsText("No past jobs found.");
  };

  const isLoading = activeBtn ? getJobs.isLoading : getJobs.isLoading;
  const isError = activeBtn ? getJobs.isError : getJobs.isError;

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
              activeBtn
                ? "bg-purple-100 text-purple-600"
                : "bg-white text-black"
            }`}
            onClick={handleActiveClick}
          >
            Active
          </button>
          <button
            type="button"
            className={`rounded-full px-4 py-2.5 text-sm font-semibold text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 hover:bg-gray-100 ${
              allBtn ? "bg-purple-100 text-purple-600" : "bg-white text-black"
            }`}
            onClick={handleAllClick}
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
                        allBtn={allBtn}
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
                  Showing{" "}
                  <span className="font-semibold text-black">{startPage}</span>{" "}
                  to <span className="font-semibold text-black">{endPage}</span>{" "}
                  of{" "}
                  <span className="font-semibold text-black">
                    {jobsData?.total}
                  </span>{" "}
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
