"use client";
import { useListContent } from "../../api/index";
import { ContentComponent } from "./ContentRow";
import { Loader } from "@mantine/core";
import { useQueryClient } from "@tanstack/react-query";
import { getCookie, setCookie } from "cookies-next";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import Error from "../../components/ErrorTab";

export default function ContentListRow(props: any) {
  const content_id = Number(props.content_id);
  const pathname = usePathname().split("/")[1];
  const [domLoaded, setDomLoaded] = useState(false);
  const CookieKey = pathname + "_content";
  const browserData =
    getCookie(CookieKey) ||
    '{"key": -1, "startPage": 1, "endPage": 1, "totalPage": 0, "offset": 0, "prevPage": true, "nextPage": true}';

  const pageJSON = JSON.parse(browserData as string);

  if (pageJSON.key !== content_id) {
    pageJSON.key = content_id;
    pageJSON.startPage = 1;
    pageJSON.endPage = 1;
    pageJSON.totalPage = 0;
    pageJSON.offset = 0;
    pageJSON.prevPage = true;
    pageJSON.nextPage = true;
  }

  const disabled = true;
  const enabled = false;
  const [startPage, setStartPage] = useState(pageJSON.startPage);
  const [endPage, setEndPage] = useState(pageJSON.endPage);
  const [totalPage, setTotalPage] = useState(pageJSON.totalPage);
  const limit = 5;
  const [offset, setOffset] = useState(pageJSON.offset);
  const [prevPage, setPrevPage] = useState(pageJSON.prevPage);
  const [nextPage, setNextPage] = useState(pageJSON.nextPage);

  const { data, isLoading, isSuccess, isError, refetch, isFetched } =
    useListContent(content_id, pathname, limit, offset);
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
    queryClient.invalidateQueries({ queryKey: ["/content/get_content_list"] });
    const refectedData = await refetch();
    if (isSuccess === true) {
      setTotalPage(refectedData.data.total);
    }
  }

  const jumpToPage = () => {
    firstPage();
    setBtnClicked(false);
  };

  const [title, setTitle] = useState("Video");

  const firstLetter = pathname.charAt(0).toUpperCase();
  const restLetter = pathname.slice(1);
  const contentNameCapitalized = firstLetter + restLetter;

  useEffect(() => {
    setDomLoaded(true);
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
      let tempTitle = data.title;
      let lastDot = tempTitle.lastIndexOf(".");
      tempTitle = tempTitle.substring(0, lastDot);
      setTitle(tempTitle);
    }

    var cookieJSON = {
      key: content_id,
      startPage: startPage,
      endPage: endPage,
      totalPage: totalPage,
      offset: offset,
      prevPage: prevPage,
      nextPage: nextPage,
    };
    setCookie(CookieKey, JSON.stringify(cookieJSON), { maxAge: 60 * 60 * 24 });
    if (btnClicked === true) {
      const nextBtn = document.getElementById("next_button");
      const nextBtnOffset = nextBtn?.offsetTop;
      window.scrollTo({ top: nextBtnOffset, behavior: "instant" });
    }
  }, [
    isFetched,
    content_id,
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
      {domLoaded === true && isLoading === false && isSuccess === true && (
        <div>
          <h1 className="text-2xl font-semibold ml-5 mb-5 text-black">
            {contentNameCapitalized + " List"}
          </h1>
          <div className="space-y-3">
            {data.data.map((data: any, index: any) => (
              <ContentComponent data={data} type={pathname} key={index} />
            ))}
          </div>
          <div className="mt-5">
            {totalPage > limit && (
              <div className="flex flex-col items-center">
                <span className="text-sm text-black ">
                  Showing{" "}
                  <span className="font-semibold text-black">{startPage}</span>{" "}
                  to <span className="font-semibold text-black">{endPage}</span>{" "}
                  of{" "}
                  <span className="font-semibold text-black">{totalPage}</span>{" "}
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
      {domLoaded === false && (
        <div className="flex mt-10 md:mt-5 justify-center">
          <Loader color="grape" variant="bars" />
        </div>
      )}
      {isLoading === true && (
        <div className="flex mt-10 md:mt-5 justify-center">
          <Loader color="grape" variant="bars" />
        </div>
      )}
      {isError === true && <Error />}
    </>
  );
}
