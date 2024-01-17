"use client";
import { useState, useEffect } from "react";
import JobsCard from "./jobsCard";

const people = [
  {
    title: "sample.mp4",
    image:
      "https://aec18cb39d6670d41651478c21c17654.r2.cloudflarestorage.com/dev-metadata/thumbnail/3/video_41799a57-02bf-4be5-88f2-41f73d2f36e6.jpg?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=620745a96c4774788d66b91651975f2d%2F20240117%2Fus-east-1%2Fs3%2Faws4_request&X-Amz-Date=20240117T060312Z&X-Amz-Expires=86400&X-Amz-SignedHeaders=host&X-Amz-Signature=3a70ac573136ab0b3e0d8ff197286c3f3b89dd86de62e29f9e7109d14284cbe6",
    tags: "original, Image Deblurring, Stem Separation,original, Image Deblurring, Stem Separation,original, Image Deblurring, Stem Separation,original, Image Deblurring, Stem Separation,original, Image Deblurring, Stem Separation",
    status: "Processing",
  },
  {
    title: "sample.mp4",
    image:
      "https://aec18cb39d6670d41651478c21c17654.r2.cloudflarestorage.com/dev-metadata/thumbnail/3/video_41799a57-02bf-4be5-88f2-41f73d2f36e6.jpg?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=620745a96c4774788d66b91651975f2d%2F20240117%2Fus-east-1%2Fs3%2Faws4_request&X-Amz-Date=20240117T060312Z&X-Amz-Expires=86400&X-Amz-SignedHeaders=host&X-Amz-Signature=3a70ac573136ab0b3e0d8ff197286c3f3b89dd86de62e29f9e7109d14284cbe6",
    tags: "original, Image Deblurring, Stem Separation,original, Image Deblurring, Stem Separation,original, Image Deblurring, Stem Separation,original, Image Deblurring, Stem Separation,original, Image Deblurring, Stem Separation",
    status: "Processing",
  },
];

export default function JobsTable() {
  const [activeBtn, setActiveBtn] = useState(true);
  const [allBtn, setAllBtn] = useState(false);

  useEffect(() => {});

  return (
    <div className="px-4 sm:px-6 lg:px-8">
      <div className="sm:flex sm:items-center">
        <div className="sm:flex-auto">
          <h1 className="text-2xl font-semibold ml-5 mb-5 text-black">Jobs</h1>
        </div>
      </div>
      <div className="mt-1 flex flex-col">
        <div className="-my-2 -mx-4 overflow-x-auto sm:-mx-6 lg:-mx-8">
          <div className="inline-block min-w-full py-2 align-middle md:px-6 lg:px-8">
            <div className="space-x-2 flex justify-end">
              <button
                type="button"
                className={`rounded-full px-4 py-2.5 text-sm font-semibold text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 hover:bg-gray-100 ${
                  activeBtn
                    ? "bg-purple-100 text-purple-600"
                    : "bg-white text-black"
                }`}
                onClick={() => {
                  setActiveBtn(true);
                  setAllBtn(false);
                }}
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
                onClick={() => {
                  setAllBtn(true);
                  setActiveBtn(false);
                }}
              >
                All
              </button>
            </div>
            <div className="">
              <div className="flex flex-col mt-2">
                {people.map((person: any, index: any) => (
                  <JobsCard data={person} key={index} />
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
