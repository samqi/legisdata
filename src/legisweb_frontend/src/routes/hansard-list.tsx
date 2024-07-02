import { Link, useLoaderData } from "react-router-dom";
import { Hansard } from "../schema";

export default function HansardList() {
  // @ts-expect-error fetching API
  const hansards: Array<Hansard> = useLoaderData();

  return (
    <>
      <h1>List of Hansards</h1>
      <ul>
        {hansards.map((hansard, index) => (
          <li key={index}>
            <Link to={"/hansard/".concat(hansard.id.toString())}>
              Hansard #{hansard.id}
            </Link>
          </li>
        ))}
      </ul>
    </>
  );
}
