import * as React from "react";
import Modal from "@mui/material/Modal";
import { Button } from "@mui/material";
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
              <Button
                variant="outlined"
                onClick={() => {
                  props.setOpen(false);
                }}
                color="warning"
              >
                No
              </Button>
              <Button
                variant="contained"
                color="secondary"
                onClick={async () => {
                  localStorage.clear();
                  document.cookie.split(";").forEach((c) => {
                    document.cookie = c
                      .replace(/^ +/, "")
                      .replace(/=.*/, `=;expires=${new Date().toUTCString()};path=/`);
                  });
                  await logout(jwt)
                }}
              >
                Yes
              </Button>
            </div>
          </div>
        </div>
      </Modal>
    </div>
  );
}
