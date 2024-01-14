"use client";
import GradientBar from "../components/GradientComponent/GradientBar";
import { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { Loader } from "@mantine/core";
import { useQueryClient } from "@tanstack/react-query";

export default function Forgot() {
  const [counter, setCounter] = useState(5);
  const searchParams = useSearchParams();
  const user_id = searchParams.get("user_id");
  const email_token = searchParams.get("email_token");
  const [missing, setMissing] = useState(false);

  const queryClient = useQueryClient();

  const { data, isLoading, isSuccess, isError, refetch } = useQuery({
    queryKey: [
      `/auth/verifyemail/?user_id=${user_id}&email_token=${email_token}`,
    ],
    queryFn: async () => {
      const url = `${process.env.BASEURL}/auth/verifyemail/?user_id=${user_id}&email_token=${email_token}`;
      const response = await fetch(url, {
        method: "GET",
      });
      const data = await response.json();
      return data;
    },
    enabled: false,
  });

  useEffect(() => {
    queryClient.invalidateQueries(["verifyUser"]);
    if (user_id && email_token) {
      refetch();
    } else {
      setMissing(true);
    }
    const timer =
      counter > 0 && setInterval(() => setCounter(counter - 1), 1000);
    if (counter === 0) {
      window.location.href = "/";
    }
    return () => clearInterval(timer as any);
  }, [counter, isLoading, isSuccess, isError, data, missing]);

  return (
    <div className="grid lg:grid-cols-[30%_70%] w-full">
      <GradientBar />
      <div className="w-full h-full flex justify-center items-center">
        <div className="flex-col justify-center items-center text-black">
          {isLoading === true && missing === false && (
            <div>
              <Loader color="grape" variant="dots" />
            </div>
          )}
          {isSuccess === true && (
            <div>
              <h1 className="text-center font-semibold text-2xl lg:text-3xl mt-[2em] lg:mt-0 tracking-tight">
                Email Verified
              </h1>
              <p className="text-center font-normal text-lg lg:text-xl mt-2 lg:mt-3 text-gray-400 tracking-tight">
                {`You will be redirected in ${counter} seconds...`}
              </p>
            </div>
          )}
          {(missing === true || isError === true) && (
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
