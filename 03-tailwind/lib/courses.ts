export type Course = {
  id: string;
  title: string;
  description: string;
  credits: number;
  isElective: boolean;
  likes: number;
};

const courses: Course[] = [
  { id: "fullstack", title: "Full Stack Development", description: "React 19, Server Components, and the App Router.", credits: 5, isElective: true, likes: 24 },
  { id: "eda", title: " Exploratory Data Analysis", description: "Data visualization, feature engineering, and data cleaning.", credits: 5, isElective: false, likes: 19 },
  { id: "databases-theory", title: "Advanced database theory", description: "Relational algebra, normalization, and query optimization.", credits: 5, isElective: false, likes: 15 },
  { id: "OR", title: "Operations Research", description: "Linear programming, integer programming, and network flows.", credits: 4, isElective: true, likes: 11 },
  { id: "algorithms", title: "Algorithm Design and Analysis", description: "Greedy algorithms, dynamic programming, and NP-completeness.", credits: 4, isElective: false, likes: 21 },
  { id: "advanced-web-tech", title: "Advanced WEB technology", description: "Web components, service workers, and progressive web apps.", credits: 5, isElective: true, likes: 32 },
];

function delay<T>(value: T, ms = 300): Promise<T> {
  return new Promise((resolve) => setTimeout(() => resolve(value), ms));
}

export async function getCourses(): Promise<Course[]> {
  return delay(courses);
}

export async function getCourse(id: string): Promise<Course | undefined> {
  return delay(courses.find((course) => course.id === id));
}
