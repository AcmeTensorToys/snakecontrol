#include <sys/epoll.h>
#include <sys/types.h>
#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

int
main(int argc, char **argv) {

	int fd;
	int efd;
	int tmo;
	struct epoll_event ev;

	if (argc <= 2) {
		fprintf(stderr, "Need fd and timeout\n");
		exit(1);
	}

	fd = atoi(argv[1]);
	if (fd < 0) {
		fprintf(stderr, "Invalid fd\n");
		exit(1);
	}

	tmo = atoi(argv[2]);

	if ((efd = epoll_create1(0)) < 0) {
		fprintf(stderr, "epoll_create1 failed: %d\n", errno);
		exit(1);
	}

	ev.events = EPOLLPRI | EPOLLET;
	ev.data.fd = fd;
	if (epoll_ctl(efd, EPOLL_CTL_ADD, fd, &ev) < 0) {
		fprintf(stderr, "epoll_ctl ADD failed: %d\n", errno);
		exit(1);
	}

	while(1) {
		int er, rr;
		char buf[8] = {0, };

		memset(&ev, 0, sizeof(ev));

		er = epoll_wait(efd, &ev, 1, tmo);

		if (er < 0) {
			fprintf(stderr, "epoll_wait() failure: %d\n", errno);
			exit(2);
		}

		if (lseek(fd, 0, SEEK_SET) != 0) {
			fprintf(stderr, "lseek failed: %d\n", errno);
			exit(2);
		}

		if ((rr = read(fd, buf, sizeof(buf))) < 2) {
			fprintf(stderr, "read failed: ret=%d err=%d\n", rr, errno);
			exit(2);
		}

		if (er == 0) {
			printf("tick: %s", buf);
		} else {
			if (ev.events & EPOLLPRI) {
				printf("irq: %s", buf);
			}
		}
		
		fflush(stdout);
	}
}
