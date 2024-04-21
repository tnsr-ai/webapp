"use client";
import * as React from "react";
import Modal from "@mui/material/Modal";
import { getCookie, deleteCookie, setCookie } from "cookies-next";
import { XMarkIcon } from "@heroicons/react/20/solid";
import { Toaster, toast } from "sonner";
import { useMutation, useQueryClient } from "@tanstack/react-query";

function getCurrentDimension() {
  return {
    width: window.innerWidth,
    height: window.innerHeight,
  };
}

export default function DeletePrompt(props: any) {
  const [screenSize, setScreenSize] = React.useState({
    width: 0,
    height: 0,
  });
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

  const useDeletemutation = (id: number, type: string) => {
    const jwt = getCookie("access_token");
    return useMutation({
      mutationKey: ["delete-project", { id: id, type: type }],
      mutationFn: async () => {
        const url = `${process.env.BASEURL}/options/delete-project/${id}/${type}`;
        const response = await fetch(url, {
          method: "DELETE",
          headers: {
            Authorization: `Bearer ${jwt}`,
          },
        });
        if (!response.ok) {
          const error = await response.json();
          throw new Error(error.detail || "Network response was not ok");
        }
        return response.json();
      },
      onSuccess: () => {
        toast.success("Project deleted");
      },
      onError: (error: any) => {
        toast.error(error.message);
      },
    });
  };

  const useMutate = useDeletemutation(props.id, props.type);

  const queryClient = useQueryClient();

  React.useEffect(() => {
    if (screenSize.width === 0) {
      setScreenSize(getCurrentDimension());
    }
  }, [screenSize]);

  return (
    <div>
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
                <p className=" text-sm md:text-base break-words font-semibold text-red-500">
                  All the files inside project will be deleted
                </p>
              </div>
              <div className="flex justify-end items-center p-2 space-x-5 mt-3">
                <button
                  type="button"
                  className="rounded-md bg-white px-3.5 py-2.5 text-sm font-semibold text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 hover:bg-gray-50"
                  onClick={() => {
                    props.setDelPrompt(false);
                  }}
                >
                  No
                </button>
                <button
                  type="button"
                  className="rounded-md bg-purple-600 px-3.5 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-purple-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-purple-600"
                  onClick={async () => {
                    useMutate.mutate();
                    props.setDelPrompt(false);
                    checkCookies();
                    queryClient.refetchQueries({
                      queryKey: ["/content/get_content"],
                    });
                  }}
                >
                  Yes
                </button>
              </div>
            </div>
          </div>
        </Modal>
      </div>
      <div>
        <Toaster
          position={screenSize.width <= 1030 ? "bottom-right" : "top-right"}
          richColors
        />
      </div>
    </div>
  );
}
