"use client";
import { useState, useEffect } from "react";
import JobsCard from "./jobsCard";
import { useActiveJobs, usePastJobs } from "../api";
import { Loader } from "@mantine/core";
import Error from "../components/ErrorTab";
import Image from "next/image";

interface Jobs {
  celery_id: string | null;
  content_detail: {
    created_at: number;
    id: number;
    id_related: number;
    title: string;
    tags: string;
    thumbnail: string;
    status: string;
    user_id: number;
  };
  content_id: number;
  created_at: number;
  job_id: number;
  job_name: string;
  job_process: string;
  job_status: string;
  job_type: string;
}

export default function JobsTable() {
  const [activeBtn, setActiveBtn] = useState(true);
  const [allBtn, setAllBtn] = useState(false);
  const [jobsData, setJobsData] = useState<Jobs[] | null>(null);
  const [limit, setLimit] = useState(5);
  const [offset, setOffset] = useState(0);

  const activeJobs = useActiveJobs();
  const pastJobs = usePastJobs(limit, offset);

  useEffect(() => {
    if (activeJobs.isSuccess) {
      setJobsData(activeJobs.data.data);
    }
  }, [activeJobs.isSuccess, activeJobs.data]);

  const handleActiveClick = () => {
    setActiveBtn(true);
    setAllBtn(false);
    if (activeJobs.isSuccess) {
      setJobsData(activeJobs.data.data);
    }
  };

  const handleAllClick = () => {
    setActiveBtn(false);
    setAllBtn(true);
    if (pastJobs.isSuccess) {
      setJobsData(pastJobs.data.data);
    }
  };

  const isLoading = activeBtn ? activeJobs.isLoading : pastJobs.isLoading;
  const isError = activeBtn ? activeJobs.isError : pastJobs.isError;

  return (
    <div>
      {isLoading && (
        <div className="w-full h-full flex justify-center items-center">
          <Loader color="grape" variant="bars" />
        </div>
      )}
      {jobsData && jobsData.length > 0 && (
        <div className="px-4 sm:px-6 lg:px-8">
          <div className="sm:flex sm:items-center">
            <div className="sm:flex-auto">
              <h1 className="text-2xl font-semibold ml-5 mb-5 text-black">
                Jobs
              </h1>
            </div>
          </div>
          <div className="mt-1 flex flex-col">
            <div className="-my-2 -mx-4 overflow-x-auto sm:-mx-6 lg:-mx-8">
              <div className="inline-block min-w-full py-2 align-middle md:px-6 lg:px-8">
                <div className="space-x-2 flex justify-end mr-5">
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
                      allBtn
                        ? "bg-purple-100 text-purple-600"
                        : "bg-white text-black"
                    }`}
                    onClick={handleAllClick}
                  >
                    All
                  </button>
                </div>
                <div className="">
                  <div className="flex flex-col space-y-5">
                    {jobsData.map((job: any, index: any) => (
                      <JobsCard data={job} key={index} />
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
      {jobsData && jobsData.length === 0 && (
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
            {`All quiet here! Click 'New Job' to kick things off.`}
          </p>
        </div>
      )}
      {isError && <Error />}
    </div>
  );
}
