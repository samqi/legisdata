import { Col, Row } from "react-bootstrap";
import { Link, useLoaderData } from "react-router-dom";
import { Inquiry } from "../schema";

function SubList({ subList }: { subList: Array<Inquiry> }) {
  return (
    <ul>
      {subList.map((item, idx) => (
        <li key={idx}>
          <Link to={"/inquiry/".concat(item.id.toString())}>
            #{item.number} - {item.title || "<TIDAK TERJUMPA>"}
          </Link>
        </li>
      ))}
    </ul>
  );
}

export default function InquiryList() {
  // @ts-expect-error fetching API
  const inquiries: Array<Inquiry> = useLoaderData();
  return (
    <>
      <h1>Inquiries</h1>
      <Row>
        <Col sm={12} md={6}>
          <h2>Oral Inquiries</h2>
          <SubList subList={inquiries.filter((item) => item.is_oral)} />
        </Col>
        <Col sm={12} md={6}>
          <h2>Written Inquiries</h2>
          <SubList subList={inquiries.filter((item) => !item.is_oral)} />
        </Col>
      </Row>
    </>
  );
}
