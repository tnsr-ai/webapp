import * as React from "react";
import Modal from "@mui/material/Modal";
import useAuth from "@/hooks/useAuth";
import { getCookie } from "cookies-next";
import { XMarkIcon } from "@heroicons/react/20/solid";

export default function Logout(props: any) {
  const { logout } = useAuth();
  const jwt: string = getCookie("access_token") as string;
  return (
    <div>
      <Modal
        open={props.open}
        onClose={() => {
          props.setOpen(false);
        }}
        aria-labelledby="modal-modal-title"
        aria-describedby="modal-modal-description"
      >
        <div className="h-full w-full flex justify-center items-center">
          <div className="bg-white rounded-lg p-5">
            <div className="pl-2 md:w-[456px] flex justify-between">
              <h1 className="font-semibold text-lg lg:text-2xl xl:text-3xl">
                Confirm logout
              </h1>
              <XMarkIcon
                className="w-[26px] cursor-pointer"
                onClick={() => {
                  props.setOpen(false);
                }}
              />
            </div>
            <div className="p-2">
              <h1 className="font-normal text-base md:text-lg ">
                Are you sure you want to logout?
              </h1>
            </div>
            <div className="flex justify-end items-center p-2 space-x-5 mt-3">
              <button
                type="button"
                className="rounded-md bg-white px-3.5 py-2.5 text-sm font-semibold text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 hover:bg-gray-50"
                onClick={() => {
                  props.setOpen(false);
                }}
              >
                No
              </button>
              <button
                type="button"
                className="rounded-md bg-purple-600 px-3.5 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-purple-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-purple-600"
                onClick={async () => {
                  localStorage.clear();
                  document.cookie.split(";").forEach((c) => {
                    document.cookie = c
                      .replace(/^ +/, "")
                      .replace(
                        /=.*/,
                        `=;expires=${new Date().toUTCString()};path=/`
                      );
                  });
                  await logout(jwt);
                }}
              >
                Yes
              </button>
            </div>
          </div>
        </div>
      </Modal>
    </div>
  );
}
