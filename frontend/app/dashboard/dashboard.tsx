"use client";
import Image from "next/image";
import { StarIcon } from "@heroicons/react/20/solid";
import Link from "next/link";
import { dashboardStats, networkStats } from "../constants/constants";
import PieActiveArc from "./pieChart";
import { stringify } from "querystring";

interface UserData {
  user_id: number;
  video_processed: number;
  audio_processed: number;
  image_processed: number;
  downloads: string;
  uploads: string;
  storage_used: number;
  storage_limit: number;
  gpu_usage: string;
  storage_json: string;
  created_at: number;
  updated_at: number;
  name: string;
  balance: number;
  storage: string;
  [key: string]: number | string;
}

interface DashboardContentProps {
  data: {
    detail: string;
    data: UserData;
    verified: boolean;
  };
}

export default function DashboardContent({ data }: DashboardContentProps) {
  console.log(JSON.parse(data.data.storage_json), "JSON");
  return (
    <div className="max-w-[1500px] m-auto" data-testid="dashboardContent">
      <div className="flex flex-col ">
        <div id="welcome-back" className="">
          <div className="flex-row xl:flex mt-5 px-6 gap-5 ">
            <div className="bg-purple-200 rounded-xl md:flex-[6] h-[224px] shadow-[0_3px_10px_rgb(0,0,0,0.2)]">
              <div className="flex flex-col items-center justify-center h-full">
                {data.verified === true && (
                  <h1 className="text-center font-bold italic text-2xl lg:text-3xl">
                    {`Welcome Back! ${data.data.name}`}
                  </h1>
                )}
                {data.verified === false && (
                  <h1 className="text-center font-bold italic text-2xl lg:text-3xl">
                    {`Welcome ${data.data.name}`}
                  </h1>
                )}
                <h1 className="text-center font-medium text-lg lg:text-xl mt-3">
                  One platform to enhance your media 🚀
                </h1>
              </div>
            </div>
            <div
              className="bg-[#171d26] rounded-xl mt-5 xl:mt-0 md:flex-[2] h-[224px] space-y-1 shadow-[0_3px_10px_rgb(0,0,0,0.2)]"
              id="dashboardCC"
            >
              <div className="w-[100%] h-[100%] flex justify-center items-center">
                <div className="p-5 space-y-1">
                  <h1 className="text-gray-300 text-xl xl:text-lg text-center">
                    Current Balance
                  </h1>
                  <div className="flex justify-center items-center space-x-2">
                    <StarIcon className="w-[28px] fill-yellow-500" />
                    <h1 className="text-white font-semibold text-3xl xl:text-2xl">
                      {`${data.data.balance} credits`}
                    </h1>
                  </div>
                  <Link href={"/billing"}>
                    <h1 className="text-gray-300 text-lg xl:text-base text-center cursor-pointer">
                      Buy more credits
                    </h1>
                  </Link>
                </div>
              </div>
            </div>
          </div>
        </div>
        <h1 className="px-8 mt-5 text-lg font-medium">Files</h1>
        <div id="stats" className="">
          <dl className="mt-3 grid grid-cols-1 gap-5 lg:grid-cols-3 px-8">
            {dashboardStats.map((item) => (
              <div
                key={item.id}
                className="overflow-hidden rounded-xl bg-white px-4 pt-5 pb-5 sm:px-6 sm:pt-6 shadow-[0_3px_10px_rgb(0,0,0,0.2)] m-auto w-full"
              >
                <dt>
                  <div className="absolute rounded-md w-16 h-15 flex justify-center ">
                    <Image src={item.icon} alt="" width={58} height={58} />
                  </div>
                  <p className="ml-20 truncate text-sm md:text-base font-medium text-gray-500">
                    {item.name}
                  </p>
                </dt>
                <dd className="ml-20 flex items-baseline">
                  <p className="text-lg  md:text-xl font-semibold text-gray-900">
                    {data.data[item.key]}
                  </p>
                </dd>
              </div>
            ))}
          </dl>
        </div>
      </div>
      <div className="flex-row xl:flex">
        <div className="flex-[6]">
          <div id="internet-stats" className="">
            <dl className="mt-5 grid grid-cols-1 lg:grid-cols-3 px-8 gap-5">
              <div className="col-span-2">
                <h1 className="text-lg font-medium">Network Stats</h1>
                <div className="mt-5 gap-5 grid grid-cols-1 lg:grid-cols-2">
                  {networkStats.map((item) => (
                    <div
                      key={item.id}
                      className="overflow-hidden rounded-xl bg-white px-4 pt-5 pb-5 sm:px-6 sm:pt-6 shadow-[0_3px_10px_rgb(0,0,0,0.2)] m-auto w-full"
                    >
                      <dt>
                        <div className="absolute rounded-md w-16 h-15 flex justify-center ">
                          <Image
                            src={item.icon}
                            alt=""
                            width={58}
                            height={58}
                          />
                        </div>
                        <p className="ml-20 truncate text-sm md:text-base font-medium text-gray-500">
                          {item.name}
                        </p>
                      </dt>
                      <dd className="ml-20 flex items-baseline">
                        <p className="text-base  xl:text-lg font-semibold text-gray-900 whitespace-nowrap">
                          {data.data[item.key]}
                        </p>
                      </dd>
                    </div>
                  ))}
                </div>
              </div>
              {data.data.storage_used > 0 && (
                <div className="col-span-1">
                  <h1 className="text-lg font-medium">
                    Storage Distribution (in MB)
                  </h1>
                  <div className="mt-5 px-8 mb-10">
                    <PieActiveArc
                      storageData={JSON.parse(data.data.storage_json)}
                    />
                  </div>
                </div>
              )}
            </dl>
          </div>
        </div>
      </div>
    </div>
  );
}
