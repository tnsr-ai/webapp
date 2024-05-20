"use client";
import * as React from "react";
import Modal from "@mui/material/Modal";
import { getCookie, deleteCookie, setCookie } from "cookies-next";
import { XMarkIcon } from "@heroicons/react/20/solid";
import { Toaster, toast } from "sonner";
import { useQuery, useQueryClient } from "@tanstack/react-query";

function getCurrentDimension() {
  return {
    width: window.innerWidth,
    height: window.innerHeight,
  };
}

export default function CancelPrompt(props: any) {
  const [screenSize, setScreenSize] = React.useState({
    width: 0,
    height: 0,
  });

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

  const useCancelJob = (job_id: number) => {
    const jwt = getCookie("access_token");
    return useQuery({
      queryKey: ["cancel-project"],
      queryFn: async () => {
        const url = `${process.env.BASEURL}/jobs/cancel_job/?job_id=${job_id}`;
        const response = await fetch(url, {
          method: "GET",
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
      refetchOnWindowFocus: false,
      enabled: false,
      onSuccess: () => {
        toast.success("Job Cancelled");
      },
      onError: (error: any) => {
        toast.error(error.message);
      },
    });
  };

  const queryClient = useQueryClient();

  const { data, isLoading, isSuccess, refetch, isError } = useCancelJob(
    props.job_id
  );

  React.useEffect(() => {
    if (screenSize.width === 0) {
      setScreenSize(getCurrentDimension());
    }
  }, [screenSize]);

  return (
    <div>
      <div>
        <Modal
          open={props.cancelPrompt}
          onClose={() => {
            props.setCancelPrompt(false);
          }}
          aria-labelledby="modal-modal-title"
          aria-describedby="modal-modal-description"
        >
          <div className="h-full w-full flex justify-center items-center">
            <div className="bg-white rounded-lg p-5">
              <div className="pl-2 md:w-[456px] flex justify-between">
                <h1 className="font-semibold text-lg lg:text-lg xl:text-xl">
                  Cancel this running job?
                </h1>
                <XMarkIcon
                  className="w-[26px] cursor-pointer"
                  onClick={() => {
                    props.setCancelPrompt(false);
                  }}
                />
              </div>
              <div className="p-2">
                <p className="text-sm md:text-base break-words font-semibold text-red-500">
                  This action is permanent and cannot be undone.
                </p>
              </div>
              <div className="flex justify-end items-center p-2 space-x-5 mt-3">
                <button
                  type="button"
                  className="rounded-md bg-white px-3.5 py-2.5 text-sm font-semibold text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 hover:bg-gray-50"
                  onClick={() => {
                    props.setCancelPrompt(false);
                  }}
                >
                  No
                </button>
                <button
                  type="button"
                  className="rounded-md bg-purple-600 px-3.5 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-purple-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-purple-600"
                  onClick={async () => {
                    refetch();
                    props.setCancelPrompt(false);
                    checkCookies();
                    queryClient.refetchQueries({
                      queryKey: ["/jobs/get_jobs"],
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
