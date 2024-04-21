"use client";
import Image from "next/image";
import { usePathname } from "next/navigation";
import React from "react";
import { useQueryClient } from "@tanstack/react-query";
import { Loader } from "@mantine/core";
import { Key, useEffect, useState } from "react";
import { useGetContent } from "../../api/index";
import ContentCard from "./ContentCard";
import { ArrowSmallUpIcon } from "@heroicons/react/20/solid";
import Error from "../../components/ErrorTab";
import { setCookie, getCookie } from "cookies-next";

export default function ContentList(props: any) {
  const pathname = usePathname().replace("/", "");
  const browserData =
    getCookie(usePathname().split("/")[1]) ||
    '{"startPage": 1, "endPage": 1, "totalPage": 0, "offset": 0, "prevPage": true, "nextPage": true}';

  const pageJSON = JSON.parse(browserData as string);
  const disabled = true;
  const enabled = false;
  const [startPage, setStartPage] = useState(pageJSON.startPage);
  const [endPage, setEndPage] = useState(pageJSON.endPage);
  const [totalPage, setTotalPage] = useState(pageJSON.totalPage);
  const limit = 12;
  const [offset, setOffset] = useState(pageJSON.offset);
  const [prevPage, setPrevPage] = useState(pageJSON.prevPage);
  const [nextPage, setNextPage] = useState(pageJSON.nextPage);
  const [domLoaded, setDomLoaded] = useState(false);

  const { data, isLoading, isSuccess, isFetched, refetch, isError } =
    useGetContent(limit, offset, pathname);
  const [btnClicked, setBtnClicked] = useState(false);

  const nextData = () => {
    setOffset(offset + limit);
    setStartPage(startPage + limit);
    setPrevPage(enabled);
    if (endPage + limit >= totalPage) {
      setEndPage(totalPage);
    } else {
      setEndPage(endPage + limit);
    }
    setBtnClicked(true);
  };

  const prevData = () => {
    setOffset(offset - limit);
    setNextPage(enabled);
    if (startPage - limit <= 1) {
      setStartPage(1);
      pageJSON.prevPage = false;
      setPrevPage(disabled);
    } else {
      setStartPage(startPage - limit);
    }
    if (endPage - limit <= limit) {
      setEndPage(limit);
    } else {
      setEndPage(endPage - limit);
    }
    setBtnClicked(true);
  };

  const firstPage = () => {
    setOffset(0);
    setStartPage(1);
    setEndPage(pageJSON.limit);
    setPrevPage(disabled);
    setNextPage(enabled);
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
    if (isSuccess === true && isFetched === true) {
      setTotalPage(data.total);
      if (data.total <= limit) {
        setEndPage(data.total);
        setNextPage(disabled);
      } else {
        setEndPage(startPage + limit - 1);
        setNextPage(enabled);
      }
      if (endPage >= totalPage) {
        setEndPage(totalPage);
        setNextPage(disabled);
      }
    }

    var cookieJSON = {
      startPage: startPage,
      endPage: endPage,
      totalPage: totalPage,
      offset: offset,
      prevPage: prevPage,
      nextPage: nextPage,
    };
    setCookie(pathname, JSON.stringify(cookieJSON), { maxAge: 60 * 60 * 24 });
    if (btnClicked === true) {
      const nextBtn = document.getElementById("next_button");
      const nextBtnOffset = nextBtn?.offsetTop;
      window.scrollTo({ top: nextBtnOffset, behavior: "instant" });
    }
  }, [
    isFetched,
    props.VideoUpload,
    refetch,
    isSuccess,
    data,
    btnClicked,
    startPage,
    endPage,
    totalPage,
    limit,
    offset,
    prevPage,
    nextPage,
  ]);

  return (
    <>
      {domLoaded && (
        <div className=" w-full">
          <div className="grid grid-cols-2 place-content-between ">
            <h1 className="w-max text-2xl font-semibold mt-3 ml-5 mb-5">
              {`Uploaded ${contentNameCapitalized}`}
            </h1>
            {pageJSON.startPage > 1 && (
              <div
                className="flex justify-end items-center mt-3 ml-5 mb-5 cursor-pointer"
                onClick={jumpToPage}
              >
                <p className="text-purple-500">Jump to Page 1</p>
                <ArrowSmallUpIcon className="w-[30px] h-[30px] fill-purple-500" />
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
                  {data.total > limit && (
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
