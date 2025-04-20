import Head from "../components/public/Head/page";
import About from "../components/public/About/page";
import Review from "../components/public/Review/page";
import Advantage from "../components/public/Advantage/page";
import Statistics from "../components/public/Statistics/page";
import Term from "../components/public/Term/page";

export default function Home() {
  return (
    <div>
      <Head/>
      <About/>
      <Review />
      <Advantage />
      <Statistics />
      <Term/>
    </div>
  );
}
