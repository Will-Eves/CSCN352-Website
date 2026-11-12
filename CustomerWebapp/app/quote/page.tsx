import Image from "next/image";

import {askQuote} from './action'

export default function Home(){
    return (
        <div className="flex flex-col flex-1 items-center justify-top mt-18 font-sans">
            <header className="bg-[#393a3c]/60 backdrop-blur fixed top-0 z-50 w-[100%] h-15 md:h-20 border-b-1 border-[#a7a4a9] flex flex-row justify-between items-center">
                <div className="ml-5">
                    <h1 className="text-2xl font-medium font-[Inter] italic">Rage n Raze</h1>
                </div>

                <div className="mr-5 hidden md:flex flex-row justify-right mt-1.5">
                    <a href="../" className="mx-5 text-1xl text-[#f5f3ed] hover:text-[#ffc400]">Home</a>
                    <a href="" className="mx-5 text-1xl text-[#b8b8b5]">Quote</a>
                </div>

                <div className="mr-5 flex md:hidden flex-row justify-right mt-1.5">
                    <a href="pages/" className="mx-5 text-1xl text-[#6a6459] hover:text-[#966d3a]">Pages</a>
                </div>
            </header>

            <main className="flex flex-col items-start md:items-center gap-6 p-7 md:flex-row md:gap-8 rounded-2xl mt-18">
                <div className="h-[330px] lg:h-[425px] w-[250px] md:w-[450px]">
                    <h1 className="text-3xl lg:text-4xl font-medium mb-10 font-[Inter] text-[#f5f3ed]">
                        Start the <strong className="text-[#ffc400]">Rage</strong>.
                    </h1>

                    <p className="font-[Inter] text-[12px] lg:text-[14px] text-[#f5f3ed] mb-10">
                        FASH • INEXPENSIVE • BUT NOT CHEAP
                    </p>

                    <p className="text-base lg:text-[17px] font-light my-10 text-[#b8b8b5]">
                        No matter the job, we make sure things get done <em>well</em>.{" "}
                    </p>

                    
                    <form action={askQuote} className="quote-form">
                        <div className="form-group">
                            <label htmlFor="name">Name</label>
                            <input
                                id="name"
                                name="name"
                                type="text"
                                placeholder="Your full name"
                                required
                            />
                        </div>

                        <div className="form-group">
                            <label htmlFor="email">Email</label>
                            <input
                                id="email"
                                name="email"
                                type="email"
                                placeholder="you@example.com"
                                required
                            />
                        </div>

                        <div className="form-group">
                            <label htmlFor="address">Property Address</label>
                            <input
                                id="address"
                                name="address"
                                type="text"
                                placeholder="Where is the property located?"
                                required
                            />
                        </div>

                        <div className="form-group">
                            <label htmlFor="comments">Destruction Comments</label>
                            <textarea
                                id="comments"
                                name="comments"
                                placeholder="Anything else about the project you'd like us to know?"
                                rows={5}
                                required
                            />
                        </div>

                        <button type="submit" className="quote-submit">GET A FREE QUOTE</button>
                    </form>

                </div>
            </main>
        </div>
    );
}