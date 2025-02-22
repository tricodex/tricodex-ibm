"use client"

import * as React from "react"
import {
  AudioWaveform,
  BookOpen,
  Bot,
  Command,
  Frame,
  GalleryVerticalEnd,
  Map,
  PieChart,
  Settings2,
  SquareTerminal,
  Activity,
  Users,
  HeadphonesIcon,
  LineChart,
  Network,
} from "lucide-react"

import { NavMain } from "@/components/nav-main"
import { NavProjects } from "@/components/nav-projects"
import { NavUser } from "@/components/nav-user"
import { TeamSwitcher } from "@/components/team-switcher"
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarHeader,
  SidebarRail,
} from "@/components/ui/sidebar"

const data = {
  user: {
    name: "Process Admin",
    email: "admin@processlens.com",
    avatar: "/logo-crop.png",
  },
  teams: [
    {
      name: "PL",
      logo: "/logo-crop.png",
      plan: "Enterprise",
    }
  ],
  navMain: [
    {
      title: "Process Mining",
      url: "#",
      icon: Activity,
      isActive: true,
      items: [
        {
          title: "New Analysis",
          url: "/",
        },
        {
          title: "Past Analyses",
          url: "/dashboard",
        },
      ],
    },
    {
      title: "Resources",
      url: "#",
      icon: Users,
      items: [
        {
          title: "Resource Utilization",
          url: "/resources",
        },
        {
          title: "Team Performance",
          url: "/team",
        },
      ],
    },
    {
      title: "Documentation",
      url: "#",
      icon: BookOpen,
      items: [
        {
          title: "Getting Started",
          url: "#",
        },
        {
          title: "API Reference",
          url: "#",
        },
        {
          title: "Examples",
          url: "#",
        },
      ],
    },
    {
      title: "Settings",
      url: "#",
      icon: Settings2,
      items: [
        {
          title: "General",
          url: "#",
        },
        {
          title: "API Keys",
          url: "#",
        },
        {
          title: "Notifications",
          url: "#",
        },
      ],
    },
  ],
  projects: [
    {
      name: "Customer Support",
      url: "#",
      icon: HeadphonesIcon,
    },
    {
      name: "Sales Pipeline",
      url: "#",
      icon: LineChart,
    },
    {
      name: "IT Operations",
      url: "#",
      icon: Network,
    },
  ],
}

export function AppSidebar({ ...props }: React.ComponentProps<typeof Sidebar>) {
  return (
    <Sidebar collapsible="icon" {...props}>
      <SidebarHeader className="pb-4">
        <TeamSwitcher teams={data.teams} />
      </SidebarHeader>
      <SidebarContent>
        <NavMain items={data.navMain} />
        <NavProjects projects={data.projects} />
      </SidebarContent>
      <SidebarFooter>
        <NavUser user={data.user} />
      </SidebarFooter>
      <SidebarRail />
    </Sidebar>
  )
}
