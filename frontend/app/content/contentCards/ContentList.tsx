"use client";
import Image from "next/image";
import { usePathname } from "next/navigation";
import React from "react";
import { useQueryClient } from "@tanstack/react-query";
import { Loader } from "@mantine/core";
import { Key, useEffect, useState } from "react";
import { contentEndpoints } from "@/app/api/endpoints";
import { useQuery } from "@tanstack/react-query";
import ContentCard from "./ContentCard";
import { ArrowUpIcon } from "@heroicons/react/20/solid";
import Error from "../../components/ErrorTab";
import { setCookie, getCookie } from "cookies-next";

export default function ContentList(props: any) {
  const pathname = usePathname().replace("/", "");
  const limit = 12;
  
  // Initialize with default values if cookie doesn't exist or is invalid
  const getInitialPaginationState = () => {
    try {
      const browserData = getCookie(pathname);
      if (!browserData || typeof browserData !== 'string') {
        return {
          startPage: 1,
          endPage: limit,
          totalPage: 0,
          offset: 0,
          prevPage: true,
          nextPage: true
        };
      }
      const parsed = JSON.parse(browserData);
      return {
        startPage: parsed.startPage || 1,
        endPage: parsed.endPage || limit,
        totalPage: parsed.totalPage || 0,
        offset: parsed.offset || 0,
        prevPage: parsed.prevPage !== undefined ? parsed.prevPage : true,
        nextPage: parsed.nextPage !== undefined ? parsed.nextPage : true
      };
    } catch (error) {
      return {
        startPage: 1,
        endPage: limit,
        totalPage: 0,
        offset: 0,
        prevPage: true,
        nextPage: true
      };
    }
  };

  const initialState = getInitialPaginationState();
  const [startPage, setStartPage] = useState(initialState.startPage);
  const [endPage, setEndPage] = useState(initialState.endPage);
  const [totalPage, setTotalPage] = useState(initialState.totalPage);
  const [offset, setOffset] = useState(initialState.offset);
  const [prevPage, setPrevPage] = useState(initialState.prevPage);
  const [nextPage, setNextPage] = useState(initialState.nextPage);
  const [domLoaded, setDomLoaded] = useState(false);
  const [shouldPoll, setShouldPoll] = useState(false);

  const useGetContent = (
    limit: number,
    offset: number,
    content_type: string
  ) => {
    const jwt = getCookie("access_token");
    return useQuery({
      queryKey: [
        "/content/get_content",
        { limit: limit, offset: offset, content_type: content_type },
      ],
      queryFn: async () => {
        const url = `${contentEndpoints["getContent"]}/?limit=${limit}&offset=${offset}&content_type=${content_type}`;
        const response = await fetch(url, {
          method: "GET",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${jwt}`,
          },
        });
        if (!response.ok) {
          throw `Network response was not ok. Status: ${response.status}`;
        }
        const data = await response.json();
        return data;
      },
      onSuccess: (data) => {
        const isProcessing = data.data.some(
          (content: any) => content.status === "indexing"
        );
        setShouldPoll(isProcessing);
      },
      refetchInterval: shouldPoll ? 1000 * 5 : false,
      retry: 2,
    });
  };

  const { data, isLoading, isSuccess, isFetched, refetch, isError } =
    useGetContent(limit, offset, pathname);
  const [btnClicked, setBtnClicked] = useState(false);

  const nextData = () => {
    // Prevent going beyond available data
    if (offset >= totalPage) return;
    
    const newOffset = Math.min(offset + limit, totalPage);
    const newStartPage = startPage + limit;
    let newEndPage = Math.min(endPage + limit, totalPage);
    
    setOffset(newOffset);
    setStartPage(newStartPage);
    setPrevPage(false);
    
    // Disable next button if we're at the end
    if (newOffset >= totalPage - limit || newEndPage >= totalPage) {
      setNextPage(true);
    }
    
    setEndPage(newEndPage);
    setBtnClicked(true);
  };

  const prevData = () => {
    // Prevent going before the first page
    if (offset <= 0) return;
    
    const newOffset = Math.max(0, offset - limit);
    const newStartPage = Math.max(1, startPage - limit);
    let newEndPage = Math.max(limit, endPage - limit);
    
    setOffset(newOffset);
    setNextPage(false);
    
    // Disable prev button if we're at the beginning
    if (newOffset <= 0) {
      setStartPage(1);
      setPrevPage(true);
    } else {
      setStartPage(newStartPage);
    }
    
    setEndPage(newEndPage);
    setBtnClicked(true);
  };

  const firstPage = () => {
    setOffset(0);
    setStartPage(1);
    setEndPage(Math.min(limit, totalPage || 0));
    setPrevPage(true);
    setNextPage((totalPage || 0) <= limit);
  };

  const queryClient = useQueryClient();

  async function refetchAndSetTotal() {
    queryClient.refetchQueries({ queryKey: ["/content/get_content"] });
    const refectedData = await refetch();
    if (isSuccess === true) {
      setTotalPage(refectedData.data.total);
      props.setVideoUpload(false);
    }
  }

  const jumpToPage = () => {
    firstPage();
    setBtnClicked(false);
  };

  const firstLetter = pathname.charAt(0).toUpperCase();
  const restLetter = pathname.slice(1);
  const contentNameCapitalized = firstLetter + restLetter;

  useEffect(() => {
    setDomLoaded(true);
    
    if (props.VideoUpload === true) {
      setBtnClicked(false);
      firstPage();
      refetchAndSetTotal();
      props.setVideoUpload(false);
      return;
    }
    
    if (isSuccess === true && isFetched === true && data) {
      const newTotalPage = data.total || 0;
      setTotalPage(newTotalPage);
      
      // Handle case when current page is empty after deletion
      if (data.data.length === 0 && newTotalPage > 0) {
        // Navigate to previous page if current page is empty
        const newOffset = Math.max(0, offset - limit);
        const newStartPage = Math.max(1, startPage - limit);
        const newEndPage = Math.min(newStartPage + limit - 1, newTotalPage);
        
        setOffset(newOffset);
        setStartPage(newStartPage);
        setEndPage(newEndPage);
        setPrevPage(newOffset <= 0);
        setNextPage(newOffset + limit >= newTotalPage);
        return;
      }
      
      // Update end page based on total items and current offset
      if (newTotalPage === 0) {
        setEndPage(0);
        setNextPage(true);
        setPrevPage(true);
      } else if (newTotalPage <= limit) {
        setEndPage(newTotalPage);
        setNextPage(true);
        setPrevPage(true);
      } else {
        const calculatedEndPage = Math.min(offset + limit, newTotalPage);
        setEndPage(calculatedEndPage);
        setNextPage(offset + limit >= newTotalPage);
        setPrevPage(offset <= 0);
      }
    }
  }, [isFetched, props.VideoUpload, isSuccess, data, limit, offset, startPage]);

  // Separate effect for cookie management
  useEffect(() => {
    const cookieJSON = {
      startPage,
      endPage,
      totalPage,
      offset,
      prevPage,
      nextPage,
    };
    setCookie(pathname, JSON.stringify(cookieJSON), { maxAge: 60 * 60 * 24 });
  }, [startPage, endPage, totalPage, offset, prevPage, nextPage, pathname]);

  // Separate effect for scroll behavior
  useEffect(() => {
    if (btnClicked === true) {
      const nextBtn = document.getElementById("next_button");
      const nextBtnOffset = nextBtn?.offsetTop || 0;
      window.scrollTo({ top: nextBtnOffset, behavior: "instant" });
      setBtnClicked(false);
    }
  }, [btnClicked]);

  return (
    <>
      {domLoaded && (
        <div className=" w-full">
          <div className="grid grid-cols-2 place-content-between ">
            <h1 className="w-max text-2xl font-semibold mt-3 ml-5 mb-5">
              {`Uploaded ${contentNameCapitalized}`}
            </h1>
            {startPage > 1 && (
              <div
                className="flex justify-end items-center mt-3 ml-5 mb-5 cursor-pointer"
                onClick={jumpToPage}
              >
                <p className="text-purple-500">Jump to Page 1</p>
                <ArrowUpIcon className="w-[30px] h-[30px] fill-purple-500" />
              </div>
            )}
          </div>
          {isError === true && (
            <div className="flex justify-center items-center">
              {isError && <Error />}
            </div>
          )}
          {isLoading === true && isFetched === false && (
            <div className="flex justify-center items-center">
              <Loader color="grape" variant="dots" />
            </div>
          )}
          {isSuccess === true &&
            data.detail === "Success" &&
            data.data.length >= 1 && (
              <div>
                <div className="w-full grid grid-cols-1 md:grid-cols-2 2xl:grid-cols-3 gap-5 px-5">
                  {data.data.map(
                    (singleData: any, index: Key | null | undefined) => (
                      <div key={index} className="w-full">
                        <ContentCard data={singleData} type={pathname} />
                      </div>
                    )
                  )}
                </div>
                <div className="mt-5">
                  {data && data.total > limit && (
                    <div className="flex flex-col items-center">
                      <span className="text-sm text-black ">
                        Showing{" "}
                        <span className="font-semibold text-black">
                          {startPage}
                        </span>{" "}
                        to{" "}
                        <span className="font-semibold text-black">
                          {endPage}
                        </span>{" "}
                        of{" "}
                        <span className="font-semibold text-black">
                          {totalPage}
                        </span>{" "}
                      </span>
                      <div className="inline-flex mt-2 xs:mt-0 gap-x-2">
                        <button
                          className="flex items-center justify-center px-4 h-10 text-base font-medium text-white bg-purple-600 rounded-lg hover:bg-purple-500 disabled:bg-purple-300"
                          disabled={prevPage}
                          onClick={prevData}
                          id="prev_button"
                        >
                          <svg
                            className="w-3.5 h-3.5 mr-2"
                            aria-hidden="true"
                            xmlns="http://www.w3.org/2000/svg"
                            fill="none"
                            viewBox="0 0 14 10"
                          >
                            <path
                              stroke="currentColor"
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth="2"
                              d="M13 5H1m0 0 4 4M1 5l4-4"
                            />
                          </svg>
                          Prev
                        </button>
                        <button
                          className="flex items-center justify-center px-4 h-10 text-base font-medium text-white bg-purple-600 border-0 border-l rounded-lg hover:bg-purple-500 disabled:bg-purple-300"
                          disabled={nextPage}
                          onClick={nextData}
                          id="next_button"
                        >
                          Next
                          <svg
                            className="w-3.5 h-3.5 ml-2"
                            aria-hidden="true"
                            xmlns="http://www.w3.org/2000/svg"
                            fill="none"
                            viewBox="0 0 14 10"
                          >
                            <path
                              stroke="currentColor"
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth="2"
                              d="M1 5h12m0 0L9 1m4 4L9 9"
                            />
                          </svg>
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}
          {isSuccess === true &&
            data.detail === "Success" &&
            data.data.length === 0 && (
              <div className="flex flex-col items-center justify-center">
                <div className="w-[100px] md:w-[125px] lg:w-[150px]">
                  <Image
                    src={"/icons/empty.png"}
                    alt={"empty"}
                    width={0}
                    height={0}
                    sizes="100vw"
                    style={{
                      width: "100%",
                      height: "100%",
                      objectFit: "cover",
                    }}
                  />
                </div>
                <span className="mt-2 text-sm text-gray-400 cursor-default">
                  No {pathname} found.{" "}
                  <span className="text-purple-600">Upload a {pathname}</span>
                </span>
              </div>
            )}
        </div>
      )}
    </>
  );
}
