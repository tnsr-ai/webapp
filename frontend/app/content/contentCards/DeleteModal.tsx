"use client";
import * as React from "react";
import Modal from "@mui/material/Modal";
import { Button } from "@mui/material";
import { getCookie, deleteCookie, setCookie } from "cookies-next";
import { XMarkIcon } from "@heroicons/react/20/solid";
import { useMutation, useQueryClient } from "@tanstack/react-query";

export default function DeletePrompt(props: any) {
  const jwt: string = getCookie("access_token") as string;
  let title;
  title = props.title;
  let title_len = title.length;
  if (title_len > 30) {
    title = title.substring(0, 30) + "...";
  }

  const checkCookies = () => {
    const cookieText = getCookie(props.type);
    if (!cookieText) {
      return;
    }
    const cookieJSON = JSON.parse(cookieText as string);
    if (cookieJSON.startPage === 1 && cookieJSON.endPage === 1) {
      deleteCookie(props.type);
      return;
    }
    if (cookieJSON.startPage === cookieJSON.endPage) {
      cookieJSON.startPage = cookieJSON.startPage - 12;
      cookieJSON.endPage = cookieJSON.endPage - 1;
      cookieJSON.offset = cookieJSON.offset - 12;
      if (cookieJSON.startPage === 1) {
        cookieJSON.prevPage = true;
      }
      if (cookieJSON.endPage > cookieJSON.totalPage) {
        cookieJSON.nextPage = false;
      }
      setCookie(props.type, JSON.stringify(cookieJSON), {
        maxAge: 60 * 60 * 24,
      });

      return;
    }
  };

  const { mutate } = useMutation(
    ({ id, type }: { id: number; type: string }) => {
      const url = `${process.env.BASEURL}/options/delete-project/${id}/${type}`;
      return fetch(url, {
        method: "DELETE",
        headers: {
          Authorization: `Bearer ${jwt}`,
        },
      });
    }
  );

  const queryClient = useQueryClient();

  return (
    <div>
      <Modal
        open={props.delPrompt}
        onClose={() => {
          props.setDelPrompt(false);
        }}
        aria-labelledby="modal-modal-title"
        aria-describedby="modal-modal-description"
      >
        <div className="h-full w-full flex justify-center items-center">
          <div className="bg-white rounded-lg p-5">
            <div className="pl-2 md:w-[456px] flex justify-between">
              <h1 className="font-semibold text-lg lg:text-lg xl:text-xl">
                Delete this project?
              </h1>
              <XMarkIcon
                className="w-[26px] cursor-pointer"
                onClick={() => {
                  props.setDelPrompt(false);
                }}
              />
            </div>
            <div className="p-2">
              <p className=" text-sm md:text-base ">
                This action is permanent and cannot be undone.
              </p>
              <p className=" text-sm md:text-base font-light break-words">
                {title}
              </p>
            </div>
            <div className="flex justify-end items-center p-2 space-x-5 mt-3">
              <Button
                variant="outlined"
                onClick={() => {
                  props.setDelPrompt(false);
                }}
                color="warning"
              >
                No
              </Button>
              <Button
                variant="contained"
                color="secondary"
                onClick={() => {
                  mutate({ id: props.id, type: props.type });
                  props.setDelPrompt(false);
                  checkCookies();
                  queryClient.invalidateQueries({
                    queryKey: ["/content/get_content"],
                  });
                  window.location.reload();
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
