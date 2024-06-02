"use client";
import GradientBar from "../components/GradientComponent/GradientBar";
import { Suspense, useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Loader } from "@mantine/core";
import { useQueryClient } from "@tanstack/react-query";
import { useSearchParams } from "next/navigation";

function SearchBarFallback() {
  return <>placeholder</>;
}

function GetParams({ setUID, setEToken }: { setUID: any; setEToken: any }) {
  const searchParams = useSearchParams();

  useEffect(() => {
    const uid = searchParams.get("user_id");
    const etoken = searchParams.get("email_token");

    if (uid) setUID(uid);
    if (etoken) setEToken(etoken);
  }, [searchParams, setUID, setEToken]);

  return null;
}

export default function Forgot() {
  const [counter, setCounter] = useState(5);
  const [uid, setUID] = useState("");
  const [etoken, setEToken] = useState("");

  const user_id = uid;
  const email_token = etoken;
  const [missing, setMissing] = useState(false);

  const queryClient = useQueryClient();

  const { data, isLoading, isSuccess, isError, refetch, error } = useQuery({
    queryKey: [
      `/auth/verifyemail/?user_id=${user_id}&email_token=${email_token}`,
    ],
    queryFn: async () => {
      const url = `${process.env.BASEURL}/auth/verifyemail/?user_id=${user_id}&email_token=${email_token}`;
      const response = await fetch(url, {
        method: "GET",
      });
      if (!response.ok) {
        throw new Error(`Email verification failed: ${response.status}`);
      }
      const data = await response.json();
      return data;
    },
    enabled: false,
    retry: false,
  });

  useEffect(() => {
    queryClient.invalidateQueries(["verifyUser"]);
    if (uid && etoken) {
      setMissing(false);
      refetch();
    } else {
      setMissing(true);
    }
  }, [uid, etoken, refetch]);

  useEffect(() => {
    const timer =
      counter > 0 && setInterval(() => setCounter(counter - 1), 1000);
    if (counter === 0) {
      window.location.href = "/";
    }
    return () => clearInterval(timer as any);
  }, [counter]);

  return (
    <div className="grid lg:grid-cols-[30%_70%] w-full">
      <head>
        <title>Tnsr.ai - Verify Email</title>
      </head>
      <Suspense fallback={<SearchBarFallback />}>
        <GradientBar />
        <GetParams setUID={setUID} setEToken={setEToken} />
      </Suspense>
      <div className="w-full h-full flex justify-center items-center">
        <div className="flex-col justify-center items-center text-black">
          {isLoading && (
            <div>
              <Loader color="grape" variant="dots" />
            </div>
          )}
          {!isLoading && isSuccess && (
            <div>
              <h1 className="text-center font-semibold text-2xl lg:text-3xl mt-[2em] lg:mt-0 tracking-tight">
                Email Verified
              </h1>
              <p className="text-center font-normal text-lg lg:text-xl mt-2 lg:mt-3 text-gray-400 tracking-tight">
                {`You will be redirected in ${counter} seconds...`}
              </p>
            </div>
          )}
          {!isLoading && isError && (
            <div>
              <h1 className="text-center font-semibold text-2xl lg:text-3xl mt-[2em] lg:mt-0 tracking-tight">
                Email Not Verified
              </h1>
              <p className="text-center font-normal text-lg lg:text-xl mt-2 lg:mt-3 text-gray-400 tracking-tight">
                {`Please try again. Redirecting in ${counter} seconds...`}
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
