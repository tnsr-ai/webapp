"use client";
import Link from "next/link";
import React, { useEffect, useState } from "react";
import {
  VideoCamera,
  SpeakerWave,
  Photo,
  CreditCard,
  Briefcase,
  Cog6Tooth,
  ChartBar,
} from "styled-icons/heroicons-solid";
import { IconLogout } from "@tabler/icons-react";
import Logout from "./ModalComponents/LogoutModal";
import { usePathname } from "next/navigation";
import { useVerifyUser } from "../api/index";
import Image from "next/image";

function classNames(...classes: any) {
  return classes.filter(Boolean).join(" ");
}

const SideDrawer = () => {
  const pathname = usePathname().split("/")[1];
  const { data, isLoading, isSuccess } = useVerifyUser();

  const [run, setRun] = useState(false);
  const [drawerBtn, setDrawerBtn] = useState([
    {
      id: 1,
      icon: ChartBar,
      title: "Dashboard",
      href: "/dashboard",
      active: pathname === "dashboard" ? true : false,
      disabled: false,
    },
    {
      id: 2,
      icon: VideoCamera,
      title: "Video",
      href: "/video",
      active: pathname === "video" ? true : false,
      disabled: false,
    },
    {
      id: 3,
      icon: SpeakerWave,
      title: "Audio",
      href: "/audio",
      active: pathname === "audio" ? true : false,
      disabled: false,
    },
    {
      id: 4,
      icon: Photo,
      title: "Image",
      href: "/image",
      active: pathname === "image" ? true : false,
      disabled: false,
    },
    {
      id: 5,
      icon: CreditCard,
      title: "Billing",
      href: "/billing",
      active: pathname === "billing" ? true : false,
      disabled: false,
    },
    {
      id: 6,
      icon: Briefcase,
      title: "Jobs",
      href: "/jobs",
      active: pathname === "jobs" ? true : false,
      disabled: false,
    },
    {
      id: 7,
      icon: Cog6Tooth,
      title: "Settings",
      href: "/settings",
      active: pathname === "settings" ? true : false,
      disabled: false,
    },
  ]);

  useEffect(() => {
    if (isSuccess === true && run === false && data !== undefined) {
      const disableBtn = [2, 3, 4, 5, 6];
      if (data?.data?.verified === false) {
        drawerBtn.map((item: any) => {
          if (disableBtn.includes(item.id)) {
            item.disabled = true;
          }
        });
      }
      setDrawerBtn(drawerBtn);
      setRun(true);
    }
  }, [drawerBtn, isSuccess, run, data]);

  const [open, setOpen] = React.useState(false);
  return (
    <div className="hidden lg:block h-full ">
      <div className="w-[296px] bg-white border-r-2 border-x-gray-300 border-dashed h-full flex flex-col justify-between">
        <div id="topBar">
          <div id="userBar">
            <Link href="/dashboard">
              <div className="flex flex-row items-center mt-2">
                <Image
                  src="/assets/mainlogo.png"
                  alt="App Logo"
                  className="w-[82px] ml-2"
                  width={82}
                  height={82}
                />
                <h1 className="font-semibold text-2xl">tnsr.ai</h1>
              </div>
            </Link>
          </div>
          <div className="flex items-center justify-center" id="menuBar">
            <nav
              className="flex flex-col space-y-1 bg-white mt-10"
              aria-label="Sidebar"
            >
              {drawerBtn.map((item: any) => (
                <Link
                  key={item.title}
                  href={item.disabled === false ? item.href : "/dashboard"}
                  className={classNames(
                    item.active
                      ? "bg-purple-50 text-purple-600"
                      : "text-gray-500 hover:bg-gray-50 hover:text-gray-900",
                    "border-transparent group flex items-center px-3 py-2 text-sm font-medium border-l-4 w-[270px] h-[50px] rounded-xl",
                    item.disabled
                      ? "cursor-not-allowed opacity-50 hover:bg-gray-50"
                      : "cursor-pointer"
                  )}
                >
                  <item.icon
                    className={classNames(
                      item.active
                        ? "text-indigo-500"
                        : "text-gray-400 group-hover:text-gray-500",
                      "mr-3 flex-shrink-0 h-6 w-6",
                      item.disabled ? "opacity-50" : ""
                    )}
                    aria-hidden="true"
                  />
                  {item.title}
                </Link>
              ))}
            </nav>
          </div>
        </div>
        <div id="logoutBar" className="flex justify-center pb-5 cursor-pointer">
          <p
            key="Logout"
            onClick={() => {
              setOpen(true);
            }}
            className="text-gray-500 hover:bg-red-100 hover:text-gray-900 border-transparent group flex items-center px-3 py-2 text-sm font-medium border-l-4 w-[270px] h-[50px] rounded-xl"
          >
            <IconLogout
              className="text-gray-400 group-hover:text-gray-500 mr-3 flex-shrink-0 h-6 w-6"
              aria-hidden="true"
            />
            {"Logout"}
          </p>
          <Logout open={open} setOpen={setOpen} />
        </div>
      </div>
    </div>
  );
};

export default SideDrawer;
