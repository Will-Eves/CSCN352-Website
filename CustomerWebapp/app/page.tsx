import Image from "next/image";

import {RowCounter} from './RowCounter'
import {OurUsers} from './OurUsers'

export default async function Home(){
    return (
        <div className="flex flex-col flex-1 items-center justify-top mt-18 font-sans">
            <header className="bg-[#393a3c]/60 backdrop-blur fixed top-0 z-50 w-[100%] h-15 md:h-20 border-b-1 border-[#a7a4a9] flex flex-row justify-between items-center">
                <div className="ml-5">
                    <h1 className="text-2xl font-medium font-[Inter] italic">Rage n Raze</h1>
                </div>

                <div className="mr-5 hidden md:flex flex-row justify-right mt-1.5">
                    <a href="" className="mx-5 text-1xl text-[#b8b8b5]">Home</a>
                    <a href="/quote/" className="mx-5 text-1xl text-[#f5f3ed] hover:text-[#ffc400]">Quote</a>
                </div>

                <div className="mr-5 flex md:hidden flex-row justify-right mt-1.5">
                    <a href="pages/" className="mx-5 text-1xl text-[#6a6459] hover:text-[#966d3a]">Pages</a>
                </div>
            </header>

            <main className="flex flex-col items-start md:items-center gap-6 p-7 md:flex-row md:gap-8 rounded-2xl mt-18">
                <div className="h-[330px] lg:h-[425px] w-[250px] md:w-[450px]">
                    <h1 className="text-3xl lg:text-4xl font-medium mb-10 font-[Inter] text-[#f5f3ed]">
                        Welcome to <strong className="text-[#ffc400]">Rage n Raze</strong>.
                    </h1>

                    <p className="font-[Inter] text-[12px] lg:text-[14px] text-[#f5f3ed] mb-10">
                        RAGE • DESTRUCTION • THIRD ITEM
                    </p>

                    <p className="text-base lg:text-[17px] font-light my-10 text-[#b8b8b5]">
                        We have been in the destruction business for <strong className="text-[#ffc400]">15</strong> years.{" "}
                    </p>

                    <p className="text-base lg:text-[17px] font-light my-10 text-[#b8b8b5]">
                        We have destroyed/are destroying <strong className="text-[#ffc400]"><RowCounter></RowCounter></strong> buildings and properties.
                    </p>

                    <h1 className="text-2xl lg:text-3xl font-medium mb-10 font-[Inter] text-[#f5f3ed]">
                        Our user <strong className="text-[#ffc400]">Information</strong>!
                    </h1>

                    <p className="text-base lg:text-[17px] font-light my-10 text-[#b8b8b5]">
                        Trust us, our users <strong className="text-[#ffc400]">understood</strong> the terms and conditions when submitting a quote!
                    </p>

                    <OurUsers></OurUsers>
                </div>
            </main>
        </div>
    );
}