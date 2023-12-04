"use client";
import { Fragment, useState } from "react";
import { Menu, Transition } from "@headlessui/react";
import { ChevronDownIcon } from "@heroicons/react/20/solid";
import React from "react";
import DeletePrompt from "./DeleteModal";
import RenamePrompt from "./RenameModal";

function classNames(...classes: string[]) {
  return classes.filter(Boolean).join(" ");
}

const menuOptions = ["Rename", "Delete Project"];

export default function DropDown(props: any) {
  const [delPrompt, setDelPrompt] = useState(false);
  const [renamePrompt, setRenamePrompt] = useState(false);
  return (
    <div>
      <Menu as="div" className="relative inline-block text-left">
        <div>
          <Menu.Button className="inline-flex w-full justify-center gap-x-1.5 rounded-md bg-white px-2 py-1 text-sm font-semibold text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 hover:bg-gray-50 items-center">
            <ChevronDownIcon
              className="-mr-1 h-5 w-5 text-gray-400"
              aria-hidden="true"
            />
          </Menu.Button>
        </div>

        <Transition
          as={Fragment}
          enter="transition ease-out duration-100"
          enterFrom="transform opacity-0 scale-95"
          enterTo="transform opacity-100 scale-100"
          leave="transition ease-in duration-75"
          leaveFrom="transform opacity-100 scale-100"
          leaveTo="transform opacity-0 scale-95"
        >
          <Menu.Items className="absolute right-0 z-10 mt-2 w-56 origin-top-right bg-white shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none rounded-md overflow-hidden">
            <div className="py-1">
              {menuOptions.map((option) =>
                option === "Delete Project" ? (
                  <Menu.Item key={option}>
                    {({ active }) => (
                      <a
                        className={classNames(
                          active ? "bg-red-100 text-red-900" : "text-red-700",
                          "block px-4 py-2 text-sm cursor-pointer"
                        )}
                        onClick={() => {
                          setDelPrompt(true);
                        }}
                      >
                        {option}
                      </a>
                    )}
                  </Menu.Item>
                ) : (
                  <Menu.Item key={option}>
                    {({ active }) => (
                      <a
                        className={classNames(
                          active
                            ? "bg-gray-100 text-gray-900"
                            : "text-gray-700",
                          "block px-4 py-2 text-sm cursor-pointer"
                        )}
                        onClick={() => {
                          setRenamePrompt(true);
                        }}
                      >
                        {option}
                      </a>
                    )}
                  </Menu.Item>
                )
              )}
            </div>
          </Menu.Items>
        </Transition>
      </Menu>
      <DeletePrompt
        delPrompt={delPrompt}
        setDelPrompt={setDelPrompt}
        id={props.data.id}
        type={props.type}
        title={props.data.title}
      />
      <RenamePrompt
        renamePrompt={renamePrompt}
        setRenamePrompt={setRenamePrompt}
        id={props.data.id}
        type={props.type}
        title={props.data.title}
        project={true}
      />
    </div>
  );
}
