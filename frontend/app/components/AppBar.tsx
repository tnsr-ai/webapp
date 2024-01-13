"use client";
import Link from "next/link";
import React, { useState, useEffect } from "react";
import Hamburger from "hamburger-react";
import { usePathname } from "next/navigation";
import SwipeableDrawer from "@mui/material/SwipeableDrawer";
import { List } from "@mui/material";
import { IconLogout } from "@tabler/icons-react";
import Logout from "./ModalComponents/LogoutModal";
import {
  VideoCamera,
  SpeakerWave,
  Photo,
  CreditCard,
  Briefcase,
  Cog6Tooth,
  ChartBar,
} from "styled-icons/heroicons-solid";

function classNames(...classes: any) {
  return classes.filter(Boolean).join(" ");
}

const AppBar = () => {
  const [isOpen, setOpen] = useState(false);
  const [logoutOpen, setLogoutOpen] = useState(false);
  const [isScrolled, setIsScrolled] = useState(false);
  const pathname = usePathname().split("/")[1];

  const drawerItems = [
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
  ];

  useEffect(() => {
    const handleScroll = () => {
      if (window.scrollY > 0) {
        setIsScrolled(true);
      } else {
        setIsScrolled(false);
      }
    };
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  return (
    <div>
      <nav>
        <div className="w-full h-full flex justify-center items-center">
          <div
            className={`w-[90%] h-[70px] md:h-[80px] navbar mt-5 rounded-3xl backdrop-blur-3xl bg-opacity-40 flex flex-row items-center border-2 border-solid lg:border-none lg:invisible ${
              isScrolled ? "bg-zinc-300" : "bg-white"
            }`}
          >
            <div className="hidden lg:block lg:w-1/3"></div>
            <div className="w-full lg:w-1/3 flex justify-center items-center lg:hidden p-2">
              <div className="flex flex-row content-center items-center">
                <Link href={"/"}>
                  <img
                    src="/assets/mainlogo_trimmed.png"
                    className="w-[44px] md:w-[52px]"
                    alt="logo image"
                  />
                </Link>
                <Link href={"/"}>
                  <p className="text-black text-3xl font-bold ml-2">tnsr.ai</p>
                </Link>
              </div>
            </div>
            <div className="lg:w-1/3 block lg:hidden">
              <Hamburger toggled={isOpen} toggle={setOpen} size={26} />
            </div>
          </div>
          <SwipeableDrawer
            open={isOpen}
            onClose={() => setOpen(false)}
            onOpen={() => setOpen(true)}
            className="block lg:hidden h-full"
          >
            <List className="h-full bg-white">
              <div className="flex justify-start items-center">
                <img
                  src="/assets/mainlogo_trimmed.png"
                  className="w-[44px] md:w-[52px] ml-5"
                  alt="logo image"
                />
                <a className="text-black text-3xl font-bold ml-2" href="#">
                  tnsr.ai
                </a>
              </div>
              <div className="mt-5">
                <div>
                  {drawerItems.map((nav, index) => (
                    <Link
                      key={nav.title}
                      href={nav.disabled === false ? nav.href : "/dashboard"}
                      className={classNames(
                        nav.active
                          ? "bg-purple-50 text-purple-600"
                          : "text-gray-500 hover:bg-gray-50 hover:text-gray-900",
                        "border-transparent group flex items-center px-3 py-2 text-sm font-medium border-l-4 w-[270px] h-[50px] rounded-xl",
                        nav.disabled
                          ? "cursor-not-allowed opacity-50 hover:bg-gray-50"
                          : "cursor-pointer"
                      )}
                    >
                      <nav.icon
                        className={classNames(
                          nav.active
                            ? "text-indigo-500"
                            : "text-gray-400 group-hover:text-gray-500",
                          "mr-3 flex-shrink-0 h-6 w-6",
                          nav.disabled ? "opacity-50" : ""
                        )}
                        aria-hidden="true"
                      />
                      {nav.title}
                    </Link>
                  ))}
                </div>

                <div
                  id="logoutBar"
                  className="flex justify-center pb-5 cursor-pointer"
                >
                  <p
                    key="Logout"
                    onClick={() => {
                      setLogoutOpen(true);
                    }}
                    className="text-gray-500 hover:bg-red-100 hover:text-gray-900 border-transparent group flex items-center px-3 py-2 text-sm font-medium border-l-4 w-[270px] h-[50px] rounded-xl"
                  >
                    <IconLogout
                      className="text-gray-400 group-hover:text-gray-500 mr-3 flex-shrink-0 h-6 w-6"
                      aria-hidden="true"
                    />
                    {"Logout"}
                  </p>
                  <Logout open={logoutOpen} setOpen={setLogoutOpen} />
                </div>
              </div>
            </List>
          </SwipeableDrawer>
        </div>
      </nav>
    </div>
  );
};

export default AppBar;
